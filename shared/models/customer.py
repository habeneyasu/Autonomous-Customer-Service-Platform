import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.enum.customer_status import CustomerStatus
from shared.enum.id_type import IdType
from shared.models.address import Address
from shared.models.base import Base

if TYPE_CHECKING:
    from shared.models.account import Account
    from shared.models.one_time_password import OneTimePassword
    from shared.models.user_auth import UserAuth


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Customer(Base):
    __tablename__ = "customers"

    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    middle_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(50), nullable=False)
    id_type: Mapped[IdType] = mapped_column(
        Enum(IdType, name="id_type_enum", create_type=False, native_enum=True),
        nullable=False,
    )
    id_number: Mapped[str] = mapped_column(String(100), nullable=False)
    address_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("addresses.address_id"),
        nullable=True,
    )
    address: Mapped[Address | None] = relationship(back_populates="customer")
    user_auth: Mapped["UserAuth | None"] = relationship(
        back_populates="customer",
        uselist=False,
    )
    accounts: Mapped[list["Account"]] = relationship(back_populates="customer")
    one_time_passwords: Mapped[list["OneTimePassword"]] = relationship(
        back_populates="customer"
    )
    status: Mapped[CustomerStatus] = mapped_column(
        Enum(
            CustomerStatus,
            name="customer_status_enum",
            create_type=False,
            native_enum=True,
        ),
        nullable=False,
        server_default=text("'ACTIVE'"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=_utc_now,
    )

