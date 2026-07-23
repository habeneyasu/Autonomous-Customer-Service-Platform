"""Lightweight session context for the prototype sandwich flow."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from security.token_store import get_token_store


@dataclass
class SessionContext:
    session_id: str
    correlation_id: UUID
    customer_id: UUID | None = None
    metadata: dict = field(default_factory=dict)

    def clear_tokens(self) -> None:
        get_token_store().clear(self.session_id)
