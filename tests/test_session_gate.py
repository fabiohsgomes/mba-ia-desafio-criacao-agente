"""Primeiro incremento: uma sessão própria precisa sobreviver à recriação do serviço."""
from aurora.config import Settings
from aurora.storage.database import Database
from aurora.storage.sessions import SQLiteSessionService


async def test_session_survives_service_restart(tmp_path):
    db = Database(Settings(db_path=tmp_path / "aurora.db"))
    db.initialize()
    service = SQLiteSessionService(db)
    session = await service.create_session(
        app_name="aurora", user_id="101", state={"apartamento": "101"}
    )
    service = SQLiteSessionService(Database(db.settings))
    restored = await service.get_session(
        app_name="aurora", user_id="101", session_id=session.id
    )
    assert restored.state["apartamento"] == "101"

from google.adk.agents import Agent
from google.adk.apps import App, ResumabilityConfig
from google.adk.runners import Runner
from google.genai import types
from aurora.services.execution import Execution, current
from aurora.tools.domain import DomainTools
from helpers import ScriptedModel


def gate_runner(db, script):
    model = ScriptedModel(script=script)
    specialist = Agent(name="reservas", model=model, tools=[DomainTools(db).reservar_area])
    root = Agent(name="principal", model=model, sub_agents=[specialist])
    return Runner(app=App(name="aurora", root_agent=root,
                         resumability_config=ResumabilityConfig(is_resumable=True)),
                  session_service=SQLiteSessionService(db))


async def collect(runner, sid, content, execution):
    token = current.set(execution)
    try:
        return [e async for e in runner.run_async(user_id="101", session_id=sid, new_message=content)]
    finally:
        current.reset(token)


async def test_adk_transfer_confirmation_resume_with_shared_transaction(tmp_path):
    db = Database(Settings(db_path=tmp_path / "gate.db"))
    db.initialize()
    runner = gate_runner(db, [
        {"call": "transfer_to_agent", "args": {"agent_name": "reservas"}},
        {"call": "reservar_area", "args": {"area": "salao-de-festas", "data": "2030-04-20"}},
        {"text": "Aguardando aprovação."},
    ])
    session = await runner.session_service.create_session(app_name="aurora", user_id="101")
    await collect(runner, session.id, types.Content(role="user", parts=[types.Part(text="Reserve o salão.")]), Execution(session.id))
    pending = db.read(lambda c: db.pending(c, session.id))
    assert len(pending) == 1, "ADK deve persistir uma pendência sem executar a reserva"
    assert not any(r["data"] == "2030-04-20" for r in db.read(lambda c: db.reservations(c, "101")))
    approval = db.read(lambda c: dict(c.execute("SELECT * FROM confirmacoes WHERE id=?", (pending[0]["id"],)).fetchone()))
    # Reconstruct every runtime object, preserving only the SQLite file.
    db = Database(db.settings)
    runner = gate_runner(db, [{"text": "Reserva concluída."}])
    answer = types.Content(role="user", parts=[types.Part(function_response=types.FunctionResponse(
        name="adk_request_confirmation", id=approval["id"], response={"confirmed": True}))])
    execution = Execution(session.id, approval=approval, confirmed=True)
    events = await collect(runner, session.id, answer, execution)
    assert any(e.author == "reservas" and e.invocation_id == approval["invocation_id"] and
               any(r.name == "reservar_area" and r.response["status"] == "executada" for r in e.get_function_responses()) for e in events)
    assert len([r for r in db.read(lambda c: db.reservations(c, "101")) if r["data"] == "2030-04-20"]) == 1
    assert db.read(lambda c: db.pending(c, session.id)) == []
    assert execution.durable[0]["status"] == "executada"
