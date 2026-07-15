from uuid import UUID

from pydantic import BaseModel, Field

from shared.schemas.common import CorrelationMixin


class CustomerMessageRequest(CorrelationMixin):
    customer_id: UUID | None = None
    channel: str = Field(default="web_chat", max_length=50)
    content: str = Field(..., min_length=1, max_length=4000)
    locale: str = Field(default="en", max_length=10)
    metadata: dict | None = None


class CustomerMessageAccepted(BaseModel):
    correlation_id: UUID
    status: str = "accepted"
    queued: bool = True
