"""Escritas de domínio usadas exclusivamente dentro da unidade do evento ADK."""
import json
import sqlite3
from uuid import uuid4

from aurora.services.execution import Execution, Plan
from aurora.storage.database import Database


def apply(conn: sqlite3.Connection, db: Database, session_id: str, invocation_id: str, plan: Plan, execution: Execution) -> dict:
    apartamento = db.session_row(conn, session_id)["apartamento"]
    old = conn.execute("SELECT resultado FROM acoes WHERE session_id=? AND invocation_id=? AND tool_call_id=?", (session_id, invocation_id, plan.call_id)).fetchone()
    if old:
        return json.loads(old[0])
    approval = execution.approval
    requires = plan.action == "autorizar_visitante"
    if plan.action == "reservar_area":
        area = conn.execute("SELECT taxa_centavos FROM areas WHERE id=?", (plan.args["area"],)).fetchone()
        if area is None:
            raise ValueError("Área inválida")
        requires = area[0] > 0
    if requires:
        if not approval or approval["session_id"] != session_id or approval["tool_call_id"] != plan.call_id or approval["acao"] != plan.action or json.loads(approval["argumentos"]) != plan.args or approval["invocation_id"] != invocation_id:
            raise PermissionError("Autorização ausente ou divergente")
        row = conn.execute("SELECT estado FROM confirmacoes WHERE id=? AND session_id=?", (approval["id"], session_id)).fetchone()
        if row is None or row[0] != "pendente":
            raise PermissionError("Confirmação indisponível")
    action_id = uuid4().hex
    if requires and not execution.confirmed:
        result = {"status": "negada", "acao": plan.action}
    elif plan.action == "reservar_area":
        code = "RSV-" + uuid4().hex
        try:
            conn.execute("INSERT INTO reservas VALUES (?,?,?,?, 'ativa',?)", (code, apartamento, plan.args["area"], plan.args["data"], action_id))
            result = {"status": "executada", "codigo": code, **plan.args}
        except sqlite3.IntegrityError:
            # Only the expected area/date collision is a business refusal.
            if conn.execute("SELECT 1 FROM reservas WHERE area=? AND data=? AND status='ativa'", (plan.args["area"], plan.args["data"])).fetchone():
                result = {"status": "recusada", "motivo": "area_indisponivel"}
            else:
                raise
    elif plan.action == "autorizar_visitante":
        conn.execute("INSERT INTO visitantes VALUES (?,?,?,?,?)", (uuid4().hex, apartamento, plan.args["nome"], plan.args["data"], action_id))
        result = {"status": "executada", **plan.args}
    elif plan.action == "cancelar_minha_reserva":
        changed = conn.execute("UPDATE reservas SET status='cancelada' WHERE codigo=? AND apartamento=? AND status='ativa'", (plan.args["codigo"], apartamento)).rowcount
        result = {"status": "cancelada" if changed else "nao_encontrada"}
    else:
        raise ValueError("Ação desconhecida")
    db.fault("effect")
    if requires:
        state = "negada" if not execution.confirmed else ("aprovada_recusada" if result["status"] == "recusada" else "aprovada_executada")
        conn.execute("UPDATE confirmacoes SET estado=?,resposta=?,resultado=? WHERE id=?", (state, execution.confirmed, json.dumps(result), approval["id"]))
        db.fault("confirmation")
    conn.execute("INSERT INTO acoes VALUES (?,?,?,?,?)", (action_id, session_id, invocation_id, plan.call_id, json.dumps(result)))
    return result
