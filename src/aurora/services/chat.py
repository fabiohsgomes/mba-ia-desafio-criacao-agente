import asyncio
import time
import httpx
from contextlib import asynccontextmanager, aclosing

from google.genai import types

from aurora.services.execution import Execution, current
from aurora.storage.database import Database
from google.adk.runners import Runner
from aurora.observability import emit


class ConfirmationConflict(Exception):
    pass


class InferenceFailure(Exception):
    pass


class InferenceTimeout(Exception):
    pass


def persisted_text(results: list[dict]) -> str:
    """Apresenta somente resultados duráveis quando a geração de texto falha."""
    lines = []
    for result in results:
        status = result["status"]
        if status == "executada" and "codigo" in result:
            lines.append(f"Reserva {result['codigo']} realizada em {result['area']} para {result['data']}.")
        elif status == "executada" and "nome" in result:
            lines.append(f"Entrada de {result['nome']} autorizada para {result['data']}.")
        elif status == "pendente":
            lines.append("A solicitação aguarda resposta pela rota de confirmações.")
        elif status == "negada":
            lines.append("A solicitação foi negada, sem executar a ação.")
        elif status == "recusada":
            lines.append("Reserva recusada: a área está indisponível na data solicitada.")
        elif status == "cancelada":
            lines.append("Reserva cancelada.")
        elif status == "nao_encontrada":
            lines.append("Não foi encontrada uma reserva própria para cancelar.")
    lines.append("Não foi possível concluir a continuação do atendimento.")
    return "\n".join(lines)


class ChatService:
    def __init__(self, db: Database, runner: Runner):
        self.db = db
        self.runner = runner
        self.locks = {}

    @asynccontextmanager
    async def locked(self, sid: str):
        # Reference counts include waiters, so entries disappear safely after use.
        entry = self.locks.setdefault(sid, [asyncio.Lock(), 0])
        entry[1] += 1
        try:
            async with entry[0]:
                yield
        finally:
            entry[1] -= 1
            if entry[1] == 0:
                self.locks.pop(sid, None)

    async def response(self, sid: str, text: str) -> dict:
        pending = await self.db.aread(lambda c: self.db.pending(c, sid))
        return {"resposta": text, "confirmacoes_pendentes": pending}

    async def message(self, sid: str, text: str) -> dict:
        async with self.locked(sid):
            row = await self.db.aread(lambda c: dict(self.db.session_row(c, sid)))
            pending = await self.db.aread(lambda c: self.db.pending(c, sid))
            if pending:
                return {"resposta": "Responda à pendência pela rota de confirmações antes de continuar.", "confirmacoes_pendentes": pending}
            return await self.run(row, types.Content(role="user", parts=[types.Part(text=text)]), Execution(sid))

    async def confirm(self, sid: str, confirmation_id: str, confirmed: bool) -> dict:
        async with self.locked(sid):
            def read(conn):
                row = dict(self.db.session_row(conn, sid))
                pending = conn.execute("SELECT * FROM confirmacoes WHERE session_id=? AND id=? AND estado='pendente'", (sid, confirmation_id)).fetchone()
                if pending is None:
                    raise ConfirmationConflict
                return row, dict(pending)
            row, approval = await self.db.aread(read)
            content = types.Content(role="user", parts=[types.Part(function_response=types.FunctionResponse(
                name="adk_request_confirmation", id=approval["id"], response={"confirmed": confirmed}))])
            return await self.run(row, content, Execution(sid, approval=approval, confirmed=confirmed))

    async def run(self, row: dict, content: types.Content, execution: Execution) -> dict:
        token = current.set(execution)
        started = time.monotonic()
        texts = []
        try:
            try:
                async with aclosing(self.runner.run_async(user_id=row["apartamento"], session_id=row["id"], new_message=content)) as events:
                    async for event in events:
                        if event.content and event.author != "user":
                            texts.extend(p.text for p in event.content.parts or [] if p.text and not p.thought)
                if execution.buffered:
                    raise RuntimeError("Runner encerrou sem persistir o grupo da ação")
            except Exception as exc:
                import sqlite3
                if isinstance(exc, (sqlite3.Error, LookupError, PermissionError)):
                    raise
                # ADK workflow errors wrap the originating exception.
                cause = exc
                seen = set()
                while id(cause) not in seen:
                    seen.add(id(cause))
                    if isinstance(cause, (TimeoutError, httpx.TimeoutException, sqlite3.Error)):
                        break
                    wrapped = getattr(cause, "error", None)
                    if isinstance(wrapped, BaseException):
                        cause = wrapped
                    elif cause.__cause__ is not None:
                        cause = cause.__cause__
                    else:
                        break
                if isinstance(cause, sqlite3.Error):
                    raise cause
                if execution.durable:
                    return await self.response(row["id"], persisted_text(execution.durable))
                if isinstance(cause, (TimeoutError, httpx.TimeoutException)):
                    raise InferenceTimeout from None
                raise InferenceFailure from None
            return await self.response(row["id"], "\n".join(texts))
        finally:
            emit("adk.run", duration_ms=(time.monotonic()-started)*1000)
            current.reset(token)
