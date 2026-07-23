from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from shared.enum.id_type import IdType


class LoginRequest(BaseModel):
    username: str = Field(..., max_length=100)
    password: str = Field(..., min_length=8, max_length=128)


class LoginResponse(BaseModel):
    customer_id: UUID
    session_id: str
    session_token: str
    expires_at: datetime


class SessionBootstrapRequest(BaseModel):
    customer_id: UUID
    channel_type: str = Field(default="WEB_CHAT", max_length=50)


class SessionBootstrapResponse(BaseModel):
    session_id: str
    session_token: str
    customer_id: UUID
    expires_at: datetime


class CustomerRegister(BaseModel):
    first_name: str = Field(..., max_length=100)
    middle_name: str | None = Field(default=None, max_length=100)
    last_name: str = Field(..., max_length=100)
    email: EmailStr
    phone_number: str = Field(..., max_length=50)
    id_type: IdType
    id_number: str = Field(..., max_length=100)
    username: str = Field(..., max_length=100)
    password: str = Field(..., min_length=8, max_length=128)
    region: str | None = Field(default=None, max_length=100)
    city: str | None = Field(default=None, max_length=100)
    street: str | None = Field(default=None, max_length=255)
    postal_code: str | None = Field(default=None, max_length=20)
