from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from shared.enum.otp_status import OtpStatus


class OtpSendRequest(BaseModel):
    customer_id: UUID
    purpose: str = Field(..., max_length=100)
    correlation_id: UUID | None = None


class OtpSendResponse(BaseModel):
    otp_id: UUID
    customer_id: UUID
    purpose: str
    status: OtpStatus
    expires_at: datetime
    attempts_remaining: int
    delivery_channel: str = "WEB_CHAT"
    dev_otp_code: str | None = None


class OtpVerifyRequest(BaseModel):
    customer_id: UUID
    otp_code: str = Field(..., min_length=4, max_length=8)
    purpose: str = Field(..., max_length=100)
    correlation_id: UUID | None = None


class OtpVerifyResponse(BaseModel):
    otp_id: UUID
    customer_id: UUID
    status: OtpStatus
    attempts_remaining: int
    verified_at: datetime | None = None
