import json
import sqlite3
import time
from uuid import uuid4
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator

from aurora.agents.team import make_runner
from aurora.config import Settings
from aurora.observability import configure, emit, request_id, http_span
from aurora.services.chat import ChatService, ConfirmationConflict, InferenceFailure, InferenceTimeout
from aurora.storage.database import Database


class Body(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class SessionBody(Body):
    apartamento: str = Field(min_length=1)

    @field_validator("apartamento")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("Apartamento vazio")
        return value


class MessageBody(Body):
    texto: str = Field(min_length=1)

    @field_validator("texto")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("Texto vazio")
        return value


class ConfirmationBody(Body):
    id: str = Field(min_length=1)
    confirmado: StrictBool


ERRORS = {
    LookupError: (404, "recurso_inexistente", "Recurso inexistente."),
    ConfirmationConflict: (409, "confirmacao_invalida", "Não há confirmação pendente com esse identificador nesta sessão."),
    InferenceFailure: (502, "gemini_indisponivel", "Não foi possível concluir o atendimento."),
    InferenceTimeout: (504, "gemini_timeout", "Tempo de inferência esgotado."),
    sqlite3.Error: (503, "armazenamento_indisponivel", "Armazenamento indisponível."),
    Exception: (500, "erro_interno", "Não foi possível concluir a operação."),
}


def create_app(settings: Settings | None = None, model=None) -> FastAPI:
    configure()
    settings = settings or Settings.from_env()
    db = Database(settings)
    db.initialize()
    # Import after startup validation; no inference is performed while initializing.
    from aurora.regulation.search import RegulationSearch
    regulation = RegulationSearch(settings.data_dir / "regulamento.md")
    runner = make_runner(db, settings, model, regulation)
    chat = ChatService(db, runner)
    @asynccontextmanager
    async def lifespan(app):
        try:
            yield
        finally:
            from aurora.agents.model import AuroraGemini
            shared = runner.app.root_agent.model
            if isinstance(shared, AuroraGemini):
                await shared.api_client.aio.aclose()
                shared.api_client.close()

    app = FastAPI(title="Aurora", version="0.1.0", lifespan=lifespan)
    app.state.db, app.state.chat, app.state.runner = db, chat, runner

    async def error_handler(request, exc):
        cls = next(cls for cls in ERRORS if isinstance(exc, cls))
        status, code, text = ERRORS[cls]
        return JSONResponse(status_code=status, content={"detail": {"codigo": code, "mensagem": text, "request_id": request_id.get()}}, headers={"X-Request-ID": request_id.get()})

    for error in ERRORS:
        app.add_exception_handler(error, error_handler)

    @app.exception_handler(RequestValidationError)
    async def invalid(request, exc):
        # Do not echo user conversation or sensitive values through validation errors.
        return JSONResponse(status_code=422, content={"detail": [
            {"loc": list(e["loc"]), "type": e["type"], "msg": "Valor inválido"} for e in exc.errors()]})

    @app.middleware("http")
    async def observe(request: Request, call_next):
        rid = uuid4().hex
        token = request_id.set(rid)
        span_token = http_span.set(uuid4().hex)
        start = time.monotonic()
        status = 500
        try:
            try:
                response = await call_next(request)
            except Exception as exc:
                # Prevent the ASGI server from dumping an exception containing
                # prompts, credentials or tool arguments into its error logs.
                emit("http.error", error_class=type(exc).__name__)
                response = await error_handler(request, exc)
            response.headers["X-Request-ID"] = rid
            status = response.status_code
            return response
        finally:
            route = request.scope.get("route")
            emit("http.request", method=request.method, route=route.path if route else "unmatched", status=status, duration_ms=(time.monotonic()-start)*1000)
            http_span.reset(span_token)
            request_id.reset(token)

    @app.post("/sessoes", status_code=201)
    async def create_session(body: SessionBody):
        session = await runner.session_service.create_session(app_name="aurora", user_id=body.apartamento)
        return {"session_id": session.id}

    @app.post("/sessoes/{session_id}/mensagens")
    async def message(session_id: str, body: MessageBody):
        return await chat.message(session_id, body.texto)

    @app.post("/sessoes/{session_id}/confirmacoes")
    async def confirm(session_id: str, body: ConfirmationBody):
        return await chat.confirm(session_id, body.id, body.confirmado)

    @app.get("/sessoes/{session_id}/eventos")
    async def events(session_id: str):
        def read(conn):
            db.session_row(conn, session_id)
            return [json.loads(r[0]) for r in conn.execute("SELECT evento FROM eventos WHERE session_id=? ORDER BY sequencia", (session_id,))]
        return await db.aread(read)

    @app.get("/apartamentos/{numero}/reservas")
    async def reservations(numero: str):
        return await db.aread(lambda c: db.reservations(c, numero))

    @app.get("/apartamentos/{numero}/visitantes")
    async def visitors(numero: str):
        return await db.aread(lambda c: db.visitors(c, numero))

    return app
