import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Numeric, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.enum.transaction_status import TransactionStatus
from shared.enum.transaction_type import TransactionType
from shared.models.base import Base

if TYPE_CHECKING:
    from shared.models.account import Account


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("amount > 0", name="check_positive_amount"),
    )

    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )
    correlation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    sender_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.account_id", ondelete="RESTRICT"),
        nullable=True,
    )
    receiver_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.account_id", ondelete="RESTRICT"),
        nullable=True,
    )
    sender_account: Mapped["Account | None"] = relationship(
        back_populates="outgoing_transactions",
        foreign_keys=[sender_account_id],
    )
    receiver_account: Mapped["Account | None"] = relationship(
        back_populates="incoming_transactions",
        foreign_keys=[receiver_account_id],
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        server_default=text("'ETB'"),
    )
    transaction_type: Mapped[TransactionType] = mapped_column(
        Enum(
            TransactionType,
            name="transaction_type_enum",
            create_type=False,
            native_enum=True,
        ),
        nullable=False,
    )
    reference_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )
    status: Mapped[TransactionStatus] = mapped_column(
        Enum(
            TransactionStatus,
            name="transaction_status_enum",
            create_type=False,
            native_enum=True,
        ),
        nullable=False,
        server_default=text("'PENDING'"),
    )
    # Column name "metadata" is reserved on DeclarativeBase; map under another attr.
    transaction_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    executed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
