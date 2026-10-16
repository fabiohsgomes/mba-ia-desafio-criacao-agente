"""Validação e autorização independentes das escolhas do modelo."""
import json
import re
from datetime import date

from google.adk.tools import ToolContext

from aurora.services.execution import Plan, current
from aurora.observability import emit
from aurora.storage.database import Database


def iso_date(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("Informe data AAAA-MM-DD")
    return date.fromisoformat(value).isoformat()


class DomainService:
    def __init__(self, db: Database):
        self.db = db

    def context(self, context: ToolContext):
        execution = current.get()
        if execution is None or execution.session_id != context.session.id:
            raise PermissionError("Execução confiável ausente")
        emit("tool.execute", outcome="contexto_validado")
        return execution

    async def scoped(self, context: ToolContext, visitors: bool = False) -> list[dict]:
        self.context(context)
        def read(conn):
            number = self.db.session_row(conn, context.session.id)["apartamento"]
            return (self.db.visitors if visitors else self.db.reservations)(conn, number)
        return await self.db.aread(read)

    async def availability(self, area: str, data: str, context: ToolContext) -> dict:
        self.context(context)
        data = iso_date(data)
        def read(conn):
            if not conn.execute("SELECT 1 FROM areas WHERE id=?", (area,)).fetchone():
                return {"status": "invalida", "motivo": "area_desconhecida"}
            return {"disponivel": conn.execute("SELECT 1 FROM reservas WHERE area=? AND data=? AND status='ativa'", (area, data)).fetchone() is None}
        return await self.db.aread(read)

    async def stage(self, action: str, args: dict, context: ToolContext) -> dict:
        execution = self.context(context)
        if "data" in args:
            args["data"] = iso_date(args["data"])
        if "nome" in args and not args["nome"].strip():
            raise ValueError("Nome de visitante inválido")
        details = dict(args)
        requires = action == "autorizar_visitante"
        if action == "reservar_area":
            area = await self.db.aread(lambda c: c.execute("SELECT taxa_centavos FROM areas WHERE id=?", (args["area"],)).fetchone())
            if area is None:
                return {"status": "invalida", "motivo": "area_desconhecida"}
            requires = area[0] > 0
            details["taxa_centavos"] = area[0]
        call_id = context.function_call_id
        if not call_id:
            raise PermissionError("Chamada de tool sem identificador")
        # The ADK confirmation alone does not authorize anything: the route's
        # persisted binding and original arguments must match as well.
        authorized = False
        approval = execution.approval
        if requires and approval:
            authorized = (approval["tool_call_id"] == call_id and approval["acao"] == action and
                          approval["session_id"] == context.session.id and
                          json.loads(approval["argumentos"]) == args and
                          context.tool_confirmation is not None and
                          context.tool_confirmation.confirmed == execution.confirmed)
        proposed = requires and not authorized
        execution.plans[call_id] = Plan(call_id, action, args, details, proposed)
        if proposed:
            context.request_confirmation(hint="Responda exclusivamente pela rota de confirmações.", payload=details)
            return {"status": "pendente", "detalhes": details}
        return {"status": "aguardando_persistencia"}
