from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from shared.enum.otp_status import OtpStatus
from shared.schemas.common import ORMModel


class OneTimePasswordCreate(BaseModel):
    customer_id: UUID
    otp_code_hash: str = Field(..., max_length=255)
    purpose: str = Field(..., max_length=100)
    expires_at: datetime
    status: OtpStatus = OtpStatus.PENDING


class OneTimePasswordRead(ORMModel):
    otp_id: UUID
    customer_id: UUID
    purpose: str
    status: OtpStatus
    attempts: int
    expires_at: datetime
    created_at: datetime
