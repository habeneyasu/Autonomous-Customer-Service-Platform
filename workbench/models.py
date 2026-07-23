"""Workbench snapshot models for the Live Observability dashboard."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class TraceStep:
    t_ms: int
    label: str
    detail: str = ""
    kind: str = "info"  # info | ok | warn | block | otp


@dataclass
class ToolCard:
    tool_name: str
    endpoint: str
    llm_parameters: dict[str, Any]
    rehydrated_parameters: dict[str, Any]
    status: str
    error_code: str | None = None
    error_message: str | None = None
    blocked: bool = False


@dataclass
class WorkbenchSnapshot:
    scenario: str
    customer_id: str
    correlation_id: str
    session_id: str
    modes: dict[str, str]
    raw_message: str
    tokenized_message: str
    token_map: dict[str, str]
    intent: str
    allowed_tools: list[str]
    blocked_tools: list[str]
    tool_cards: list[ToolCard] = field(default_factory=list)
    timeline: list[TraceStep] = field(default_factory=list)
    reply: str = ""
    otp_listening: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
