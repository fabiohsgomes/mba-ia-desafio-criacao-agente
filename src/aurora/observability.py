"""Somente metadados operacionais de uma lista fechada são emitidos."""
import contextvars
import json
import logging
from datetime import datetime, timezone
from uuid import uuid4

request_id = contextvars.ContextVar("request_id", default="")
active_agent = contextvars.ContextVar("active_agent", default="")
http_span = contextvars.ContextVar("http_span", default="")
logger = logging.getLogger("aurora")


def emit(event: str, **fields) -> None:
    allowed = {"outcome", "duration_ms", "status", "method", "route", "agent", "attempts", "error_class"}
    logger.info(json.dumps({
        "timestamp": datetime.now(timezone.utc).isoformat(), "event": event,
        "request_id": request_id.get(), "trace_id": request_id.get(),
        "span_id": http_span.get() if event == "http.request" else uuid4().hex,
        "parent_span_id": http_span.get() if event != "http.request" else None, **{k: v for k, v in fields.items() if k in allowed}
    }))


def configure() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    # Libraries may log full prompts or responses even at WARNING/ERROR.
    for name in ("google_adk", "google.adk", "google_genai", "google.genai", "httpx", "httpcore", "uvicorn.access"):
        dependency = logging.getLogger(name)
        dependency.handlers = [logging.NullHandler()]
        dependency.propagate = False
        dependency.setLevel(logging.CRITICAL + 1)
