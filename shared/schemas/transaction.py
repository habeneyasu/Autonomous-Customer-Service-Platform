from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from shared.constants.currency import DEFAULT_CURRENCY
from shared.constants.limits import (
    DEFAULT_TRANSACTION_HISTORY_LIMIT,
    MAX_TRANSACTION_HISTORY_LIMIT,
)
from shared.enum.transaction_status import TransactionStatus
from shared.enum.transaction_type import TransactionType
from shared.schemas.common import AliasModel, ORMModel


class TransactionCreate(BaseModel):
    correlation_id: UUID
    sender_account_id: UUID | None = None
    receiver_account_id: UUID | None = None
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default=DEFAULT_CURRENCY, min_length=3, max_length=3)
    transaction_type: TransactionType
    reference_number: str = Field(..., max_length=100)
    transaction_metadata: dict[str, Any] | None = None


class TransferRequest(BaseModel):
    sender_account_id: UUID
    receiver_account_id: UUID
    amount: Decimal = Field(..., gt=0)
    correlation_id: UUID | None = None
    currency: str = Field(default=DEFAULT_CURRENCY, min_length=3, max_length=3)


class ExecuteP2PTransferRequest(AliasModel):
    """Authenticated peer-to-peer transfer requiring a verified OTP."""

    sender_account_id: UUID = Field(..., alias="senderAccountId")
    receiver_account_id: UUID = Field(..., alias="receiverAccountId")
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default=DEFAULT_CURRENCY, min_length=3, max_length=3)
    otp_code: str = Field(..., min_length=4, max_length=8, alias="otpCode")
    correlation_id: UUID | None = Field(default=None, alias="correlationId")

    def to_transfer_request(self) -> TransferRequest:
        return TransferRequest(
            sender_account_id=self.sender_account_id,
            receiver_account_id=self.receiver_account_id,
            amount=self.amount,
            currency=self.currency,
            correlation_id=self.correlation_id,
        )


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
    transaction_metadata: dict[str, Any] | None = Field(default=None)
    created_at: datetime
    executed_at: datetime | None


class TransactionHistoryRequest(BaseModel):
    limit: int = Field(
        default=DEFAULT_TRANSACTION_HISTORY_LIMIT,
        ge=1,
        le=MAX_TRANSACTION_HISTORY_LIMIT,
    )
    offset: int = Field(default=0, ge=0)


class TransactionHistoryResponse(AliasModel):
    customer_id: UUID = Field(..., alias="customerId")
    transactions: list[TransactionRead]
    total_returned: int = Field(..., alias="totalReturned")
    limit: int
    offset: int
