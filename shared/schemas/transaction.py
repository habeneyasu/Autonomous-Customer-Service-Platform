from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from shared.constants.currency import DEFAULT_CURRENCY
from shared.enum.transaction_status import TransactionStatus
from shared.enum.transaction_type import TransactionType
from shared.schemas.common import ORMModel


class TransactionCreate(BaseModel):
    correlation_id: UUID
    sender_account_id: UUID | None = None
    receiver_account_id: UUID | None = None
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default=DEFAULT_CURRENCY, min_length=3, max_length=3)
    transaction_type: TransactionType
    reference_number: str = Field(..., max_length=100)
    transaction_metadata: dict[str, Any] | None = None


class TransactionRead(ORMModel):
    transaction_id: UUID
    correlation_id: UUID
    sender_account_id: UUID | None
    receiver_account_id: UUID | None
    amount: Decimal
    currency: str
    transaction_type: TransactionType
    reference_number: str
    status: TransactionStatus
    # The ORM attribute is transaction_metadata (mapped to the "metadata" column).
    transaction_metadata: dict[str, Any] | None = Field(default=None)
    created_at: datetime
    executed_at: datetime | None

    @model_validator(mode="before")
    @classmethod
    def _coerce_metadata(cls, data: Any) -> Any:
        """Handle ORM objects where the attribute is transaction_metadata."""
        if hasattr(data, "__dict__"):
            return data
        return data
