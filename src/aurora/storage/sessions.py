"""Adaptador ADK 2.12.0; append_event é a barreira antes da próxima inferência.

Tools preparam intenções. O evento de resultado aplica e persiste a ação usando
uma conexão. Propostas aguardam o evento adk_request_confirmation para gravar
ambos os eventos e o vínculo de retomada juntos. Respostas externas também são
bufferizadas até o resultado original, evitando consumir autorização sem efeito.
"""
import json
import time
from uuid import uuid4

from google.adk.events import Event
from google.adk.sessions import BaseSessionService, Session
from google.adk.sessions.base_session_service import GetSessionConfig, ListSessionsResponse

from aurora.services.execution import current
from aurora.observability import emit
from aurora.storage.actions import apply
from aurora.storage.database import Database


class SQLiteSessionService(BaseSessionService):
    def __init__(self, db: Database):
        self.db = db

    async def create_session(self, *, app_name: str, user_id: str, state: dict | None = None, session_id: str | None = None) -> Session:
        session = Session(id=session_id or uuid4().hex, app_name=app_name, user_id=user_id,
                          state={**(state or {}), "apartamento": user_id}, last_update_time=time.time())
        def create(conn):
            self.db.apartment(conn, user_id)
            conn.execute("INSERT INTO sessoes(id,app_name,apartamento,estado,atualizado) VALUES (?,?,?,?,?)", (session.id, app_name, user_id, json.dumps(session.state), session.last_update_time))
        await self.db.awrite(create)
        return session

    async def get_session(self, *, app_name: str, user_id: str, session_id: str, config: GetSessionConfig | None = None) -> Session | None:
        def get(conn):
            row = conn.execute("SELECT * FROM sessoes WHERE id=? AND app_name=? AND apartamento=?", (session_id, app_name, user_id)).fetchone()
            if not row:
                return None
            events = [Event.model_validate_json(r[0]) for r in conn.execute("SELECT evento FROM eventos WHERE session_id=? ORDER BY sequencia", (session_id,))]
            if config:
                if config.after_timestamp is not None:
                    events = [e for e in events if e.timestamp >= config.after_timestamp]
                if config.num_recent_events is not None:
                    events = events[-config.num_recent_events:] if config.num_recent_events else []
            state = json.loads(row["estado"])
            state["apartamento"] = row["apartamento"]
            return Session(id=session_id, app_name=app_name, user_id=user_id, state=state, events=events, last_update_time=row["atualizado"])
        return await self.db.aread(get)

    async def list_sessions(self, *, app_name: str, user_id: str | None = None) -> ListSessionsResponse:
        def get(conn):
            rows = conn.execute("SELECT * FROM sessoes WHERE app_name=? AND (? IS NULL OR apartamento=?) ORDER BY atualizado,id", (app_name, user_id, user_id))
            return ListSessionsResponse(sessions=[Session(id=r["id"], app_name=app_name, user_id=r["apartamento"], state=json.loads(r["estado"]), last_update_time=r["atualizado"]) for r in rows])
        return await self.db.aread(get)

    async def delete_session(self, *, app_name: str, user_id: str, session_id: str) -> None:
        await self.db.awrite(lambda c: c.execute("DELETE FROM sessoes WHERE id=? AND app_name=? AND apartamento=?", (session_id, app_name, user_id)).rowcount)

    async def append_event(self, session: Session, event: Event) -> Event:
        if event.partial:
            return event
        execution = current.get()
        if execution and execution.session_id != session.id:
            raise PermissionError("Contexto de sessão divergente")
        # The apartment column is authoritative, and cannot be changed by state deltas.
        event.actions.state_delta.pop("apartamento", None)
        await super().append_event(session, event)
        session.last_update_time = event.timestamp
        responses = event.get_function_responses()
        calls = event.get_function_calls()
        proposal = bool(execution and any(execution.plans.get(r.id) and execution.plans[r.id].proposed for r in responses))
        external_answer = bool(execution and execution.approval and event.author == "user")
        confirmation_call = any(c.name == "adk_request_confirmation" for c in calls)
        group = [*(execution.buffered if execution else []), event]
        group_has_request = any(c.name == "adk_request_confirmation" for e in group for c in e.get_function_calls())
        group_has_proposal_response = bool(execution and any(
            execution.plans.get(r.id) and execution.plans[r.id].proposed
            for e in group for r in e.get_function_responses()))
        if external_answer or ((proposal or confirmation_call) and not (group_has_request and group_has_proposal_response)):
            execution.buffered.append(event)
            return event
        responses = [r for item in group for r in item.get_function_responses()]
        results = []
        def commit(conn):
            row = self.db.session_row(conn, session.id)
            for response in responses:
                plan = execution.plans.get(response.id) if execution else None
                if plan and not plan.proposed:
                    result = apply(conn, self.db, session.id, event.invocation_id, plan, execution)
                    response.response = result
                    results.append(result)
            for call in (c for item in group for c in item.get_function_calls()):
                if call.name != "adk_request_confirmation":
                    continue
                original = call.args["originalFunctionCall"]
                plan = execution.plans.get(original["id"]) if execution else None
                if plan is None or not plan.proposed or plan.args != original["args"] or plan.action != original["name"]:
                    raise PermissionError("Proposta sem intenção validada")
                conn.execute("INSERT INTO confirmacoes(id,session_id,invocation_id,autor,tool_call_id,acao,argumentos,detalhes) VALUES (?,?,?,?,?,?,?,?)", (call.id, session.id, event.invocation_id, event.author, plan.call_id, plan.action, json.dumps(plan.args), json.dumps(plan.details)))
                results.append({"status": "pendente", "acao": plan.action, "detalhes": plan.details})
            # State is serialized only after complete grouped deltas have been applied.
            state = {k: v for k, v in session.state.items() if not k.startswith("temp:")}
            state["apartamento"] = row["apartamento"]
            conn.execute("UPDATE sessoes SET estado=?,versao=versao+1,atualizado=? WHERE id=?", (json.dumps(state), event.timestamp, session.id))
            self.db.fault("state")
            seq = conn.execute("SELECT coalesce(max(sequencia),0) FROM eventos WHERE session_id=?", (session.id,)).fetchone()[0]
            for offset, item in enumerate(group, 1):
                conn.execute("INSERT INTO eventos VALUES (?,?,?,?,?,?)", (session.id, seq+offset, item.id, item.invocation_id, item.author, item.model_dump_json()))
            conn.execute("INSERT INTO execucoes VALUES (?,?,?,?) ON CONFLICT(session_id,invocation_id) DO UPDATE SET autor=excluded.autor,checkpoint=excluded.checkpoint", (session.id, event.invocation_id, event.author, event.model_dump_json()))
            self.db.fault("events")
        await self.db.awrite(commit)
        if execution:
            execution.buffered.clear()
            execution.durable.extend(results)
            for result in results:
                if result.get("motivo") == "area_indisponivel":
                    emit("reservation.conflict", outcome="area_data_ocupada")
                if execution.approval:
                    emit("confirmation.outcome", outcome=result["status"])
            for response in responses:
                plan = execution.plans.get(response.id)
                if plan and not plan.proposed:
                    execution.plans.pop(response.id)
        return event
