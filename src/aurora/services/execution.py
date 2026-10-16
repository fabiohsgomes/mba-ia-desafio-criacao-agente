"""Contexto confiável da requisição, compartilhado pelas tasks de tools do ADK."""
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Plan:
    call_id: str
    action: str
    args: dict[str, Any]
    details: dict[str, Any]
    proposed: bool = False


@dataclass
class Execution:
    session_id: str
    approval: dict | None = None
    confirmed: bool = False
    plans: dict[str, Plan] = field(default_factory=dict)
    buffered: list = field(default_factory=list)
    durable: list[dict] = field(default_factory=list)


current: ContextVar[Execution | None] = ContextVar("aurora_execution", default=None)
