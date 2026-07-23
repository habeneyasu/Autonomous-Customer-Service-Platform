"""Shared helpers for MCP tool handlers."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.orm import Session

from shared.config.database import SessionLocal
from shared.schemas.mcp import CustomerContext


def require_customer_id(customer_context: CustomerContext | None) -> UUID:
    """Resolve authenticated customer id from platform context (never from LLM params)."""
    if customer_context is None:
        raise ValueError("customerContext is required")
    return UUID(str(customer_context.customer_id))


@contextmanager
def db_session() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def dump_model(model: BaseModel, *, by_alias: bool = False) -> dict[str, Any]:
    return model.model_dump(mode="json", by_alias=by_alias)


def run_with_db(
    customer_context: CustomerContext | None,
    action: Callable[[Session, UUID], BaseModel],
    *,
    by_alias: bool = False,
) -> dict[str, Any]:
    customer_id = require_customer_id(customer_context)
    with db_session() as db:
        return dump_model(action(db, customer_id), by_alias=by_alias)
