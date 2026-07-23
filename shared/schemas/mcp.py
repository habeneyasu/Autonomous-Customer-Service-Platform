from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import Field

from shared.schemas.common import AliasModel


class ChannelType(str, Enum):
    WEB_CHAT = "WEB_CHAT"


class McpStatus(str, Enum):
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    UNAUTHORIZED = "UNAUTHORIZED"
    UNAVAILABLE = "UNAVAILABLE"


class CustomerContext(AliasModel):
    customer_id: str = Field(..., min_length=1, alias="customerId")
    session_id: str = Field(..., min_length=1, alias="sessionId")
    auth_token: str = Field(..., min_length=1, alias="authToken")
    authenticated_at: datetime = Field(..., alias="authenticatedAt")
    channel_type: ChannelType = Field(default=ChannelType.WEB_CHAT, alias="channelType")


class McpToolRequest(AliasModel):
    tool_name: str = Field(..., min_length=1, alias="toolName")
    correlation_id: UUID = Field(..., alias="correlationId")
    customer_context: CustomerContext = Field(..., alias="customerContext")
    parameters: dict = Field(default_factory=dict)
    requested_at: datetime = Field(..., alias="requestedAt")


class McpError(AliasModel):
    code: str | None = None
    message: str | None = None
    retryable: bool = False


class McpToolResponse(AliasModel):
    tool_name: str = Field(..., alias="toolName")
    correlation_id: UUID = Field(..., alias="correlationId")
    status: McpStatus
    data: dict | list | None = None
    error: McpError | None = None
    executed_at: datetime = Field(..., alias="executedAt")
    execution_time_ms: int = Field(..., alias="executionTimeMs")


class McpToolDescriptor(AliasModel):
    name: str
    description: str
    state_modifying: bool = Field(..., alias="stateModifying")
    authorized_intents: list[str] = Field(default_factory=list, alias="authorizedIntents")
