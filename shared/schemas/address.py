from uuid import UUID

from pydantic import BaseModel, Field

from shared.schemas.common import ORMModel


class AddressCreate(BaseModel):
    region: str = Field(..., max_length=100)
    city: str = Field(..., max_length=100)
    street: str | None = Field(default=None, max_length=255)
    postal_code: str | None = Field(default=None, max_length=20)


class AddressUpdate(BaseModel):
    region: str | None = Field(default=None, max_length=100)
    city: str | None = Field(default=None, max_length=100)
    street: str | None = Field(default=None, max_length=255)
    postal_code: str | None = Field(default=None, max_length=20)


class AddressRead(ORMModel):
    address_id: UUID
    region: str
    city: str
    street: str | None
    postal_code: str | None
