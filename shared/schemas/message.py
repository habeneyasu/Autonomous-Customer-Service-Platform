from uuid import UUID

from pydantic import BaseModel, Field


class CustomerMessageRequest(BaseModel):
    """Inbound customer chat payload (raw text; never forwarded to the LLM)."""

    correlation_id: UUID | None = None
    customer_id: UUID | None = None
    channel: str = Field(default="web_chat", max_length=50)
    content: str = Field(..., min_length=1, max_length=4000)
    locale: str = Field(default="en", max_length=10)
    metadata: dict | None = None


class CustomerMessageAccepted(BaseModel):
    correlation_id: UUID
    session_id: str
    status: str = "accepted"
    queued: bool = True


class TokenizedMessage(BaseModel):
    """LLM-safe payload after Zone 2 tokenization."""

    session_id: str
    tokenized_content: str
    tokens: dict[str, str] = Field(default_factory=dict)


class ToolCallRequest(BaseModel):
    """Agent tool intent using tokens only (Zone 3 rehydrates before execution)."""

    session_id: str
    tool_name: str
    arguments: dict = Field(default_factory=dict)
