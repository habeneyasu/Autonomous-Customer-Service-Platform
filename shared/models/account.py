import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.enum.account_status import AccountStatus
from shared.enum.account_type import AccountType
from shared.models.base import Base

if TYPE_CHECKING:
    from shared.models.customer import Customer
    from shared.models.transaction import Transaction


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (
        CheckConstraint("balance >= 0", name="check_positive_balance"),
    )

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.customer_id", ondelete="CASCADE"),
        nullable=False,
    )
    customer: Mapped["Customer"] = relationship(back_populates="accounts")
    account_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    account_type: Mapped[AccountType] = mapped_column(
        Enum(AccountType, name="account_type_enum", create_type=False, native_enum=True),
        nullable=False,
        server_default=text("'SAVINGS'"),
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        server_default=text("'ETB'"),
    )
    balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        server_default=text("0.00"),
    )
    status: Mapped[AccountStatus] = mapped_column(
        Enum(
            AccountStatus,
            name="account_status_enum",
            create_type=False,
            native_enum=True,
        ),
        nullable=False,
        server_default=text("'ACTIVE'"),
    )
    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    outgoing_transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="sender_account",
        foreign_keys="Transaction.sender_account_id",
    )
    incoming_transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="receiver_account",
        foreign_keys="Transaction.receiver_account_id",
    )
