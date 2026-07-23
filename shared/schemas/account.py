from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from shared.constants.currency import DEFAULT_CURRENCY
from shared.enum.account_status import AccountStatus
from shared.enum.account_type import AccountType
from shared.schemas.common import AliasModel, ORMModel


class AccountCreate(BaseModel):
    customer_id: UUID
    account_number: str = Field(..., max_length=50)
    account_type: AccountType = AccountType.SAVINGS
    currency: str = Field(default=DEFAULT_CURRENCY, min_length=3, max_length=3)
    balance: Decimal = Field(default=Decimal("0.00"), ge=0)
    status: AccountStatus = AccountStatus.ACTIVE


class AccountUpdate(BaseModel):
    account_type: AccountType | None = None
    status: AccountStatus | None = None


class FreezeAccountRequest(AliasModel):
    account_id: UUID | None = Field(default=None, alias="accountId")
    otp_code: str = Field(..., min_length=4, max_length=8, alias="otpCode")
    reason: str | None = Field(default=None, max_length=255)


class FreezeAccountResponse(AliasModel):
    account_id: UUID = Field(..., alias="accountId")
    account_number: str = Field(..., alias="accountNumber")
    customer_id: UUID = Field(..., alias="customerId")
    status: AccountStatus
    previous_status: AccountStatus = Field(..., alias="previousStatus")
    reason: str | None = None


class AccountRead(ORMModel):
    account_id: UUID
    customer_id: UUID
    account_number: str
    account_type: AccountType
    currency: str
    balance: Decimal
    status: AccountStatus
    opened_at: datetime
