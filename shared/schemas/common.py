from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    code: str
    message: str
    correlation_id: UUID | None = None


class HealthResponse(BaseModel):
    status: str = "ok"
    app_name: str
    environment: str


class TimestampMixin(BaseModel):
    created_at: datetime
    updated_at: datetime | None = None


class CorrelationMixin(BaseModel):
    correlation_id: UUID = Field(..., description="Request/workflow correlation id")
