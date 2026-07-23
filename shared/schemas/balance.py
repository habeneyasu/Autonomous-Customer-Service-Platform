from decimal import Decimal
from uuid import UUID

from pydantic import ConfigDict

from shared.enum.account_status import AccountStatus
from shared.enum.account_type import AccountType
from shared.schemas.common import ORMModel


class AccountBalanceItem(ORMModel):
    account_id: UUID
    account_number: str
    account_type: AccountType
    currency: str
    balance: Decimal
    status: AccountStatus


class CustomerBalanceResponse(ORMModel):
    model_config = ConfigDict(from_attributes=True)

    customer_id: UUID
    accounts: list[AccountBalanceItem]
    total_balance: Decimal
    currency: str
