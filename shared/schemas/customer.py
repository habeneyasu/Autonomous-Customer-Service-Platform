from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from shared.enum.customer_status import CustomerStatus
from shared.enum.id_type import IdType
from shared.schemas.common import ORMModel


class CustomerCreate(BaseModel):
    first_name: str = Field(..., max_length=100)
    middle_name: str | None = Field(default=None, max_length=100)
    last_name: str = Field(..., max_length=100)
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8, max_length=100)
    phone_number: str = Field(..., max_length=50)
    id_type: IdType
    id_number: str = Field(..., max_length=100)
    address_id: UUID | None = None
    status: CustomerStatus = CustomerStatus.ACTIVE


class CustomerUpdate(BaseModel):
    first_name: str | None = Field(default=None, max_length=100)
    middle_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    email: EmailStr | None = None
    username: str | None = None
    phone_number: str | None = Field(default=None, max_length=50)
    address_id: UUID | None = None
    status: CustomerStatus | None = None


class CustomerRead(ORMModel):
    customer_id: UUID
    first_name: str
    middle_name: str | None
    last_name: str
    email: str
    username: str
    phone_number: str
    id_type: IdType
    id_number: str
    address_id: UUID | None
    status: CustomerStatus
    created_at: datetime
    updated_at: datetime
