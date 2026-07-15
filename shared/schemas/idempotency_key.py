from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from shared.schemas.common import ORMModel


class IdempotencyKeyCreate(BaseModel):
    key_hash: str = Field(..., min_length=64, max_length=64)
    correlation_id: UUID
    response_code: int
    response_body: str


class IdempotencyKeyRead(ORMModel):
    key_hash: str
    correlation_id: UUID
    response_code: int
    response_body: str
    created_at: datetime
