from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from shared.schemas.common import ORMModel


class UserAuthCreate(BaseModel):
    customer_id: UUID
    username: str = Field(..., max_length=100)
    password_hash: str = Field(..., max_length=255)
    mfa_enabled: bool = False


class UserAuthRead(ORMModel):
    user_auth_id: UUID
    customer_id: UUID
    username: str
    mfa_enabled: bool
    failed_attempts: int
    last_login_at: datetime | None
