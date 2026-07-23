from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from services.base import (
    apply_updates,
    commit_refresh,
    get_or_404,
    require_owned_account,
    verify_customer_otp,
)
from shared.constants.currency import DEFAULT_CURRENCY
from shared.constants.otp import OTP_PURPOSE_ACCOUNT_FREEZE
from shared.enum.account_status import AccountStatus
from shared.exceptions.domain import ConflictError, NotFoundError, ValidationError
from shared.models.account import Account
from shared.models.customer import Customer
from shared.schemas.account import (
    AccountCreate,
    AccountRead,
    AccountUpdate,
    FreezeAccountRequest,
    FreezeAccountResponse,
)
from shared.schemas.balance import AccountBalanceItem, CustomerBalanceResponse


class AccountService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, payload: AccountCreate) -> AccountRead:
        get_or_404(self._db, Customer, payload.customer_id, "Customer")
        if self._db.scalar(select(Account).where(Account.account_number == payload.account_number)):
            raise ConflictError(f"Account number {payload.account_number} already exists")
        account = commit_refresh(self._db, Account(**payload.model_dump()))
        return AccountRead.model_validate(account)

    def get(self, account_id: UUID) -> AccountRead:
        return AccountRead.model_validate(get_or_404(self._db, Account, account_id, "Account"))

    def list_by_customer(self, customer_id: UUID) -> list[AccountRead]:
        get_or_404(self._db, Customer, customer_id, "Customer")
        rows = self._db.scalars(
            select(Account).where(Account.customer_id == customer_id).order_by(Account.opened_at.desc())
        ).all()
        return [AccountRead.model_validate(row) for row in rows]

    def get_balance_by_customer(self, customer_id: UUID) -> CustomerBalanceResponse:
        accounts = self.list_by_customer(customer_id)
        if not accounts:
            raise NotFoundError(f"No accounts found for customer {customer_id}")
        total = sum((account.balance for account in accounts), Decimal("0.00"))
        return CustomerBalanceResponse(
            customer_id=customer_id,
            accounts=[AccountBalanceItem.model_validate(account) for account in accounts],
            total_balance=total,
            currency=accounts[0].currency or DEFAULT_CURRENCY,
        )

    def update(self, account_id: UUID, payload: AccountUpdate) -> AccountRead:
        account = get_or_404(self._db, Account, account_id, "Account")
        apply_updates(account, payload)
        return AccountRead.model_validate(commit_refresh(self._db, account))

    def freeze_account(
        self,
        customer_id: UUID,
        payload: FreezeAccountRequest,
    ) -> FreezeAccountResponse:
        if payload.account_id is None:
            raise ValidationError("accountId is required")

        verify_customer_otp(
            self._db,
            customer_id=customer_id,
            otp_code=payload.otp_code,
            purpose=OTP_PURPOSE_ACCOUNT_FREEZE,
        )

        account = require_owned_account(self._db, payload.account_id, customer_id)
        if account.status == AccountStatus.CLOSED:
            raise ValidationError("Closed accounts cannot be frozen")
        if account.status == AccountStatus.FROZEN:
            raise ConflictError("Account is already frozen")

        previous_status = account.status
        account.status = AccountStatus.FROZEN
        commit_refresh(self._db, account)

        return FreezeAccountResponse(
            accountId=account.account_id,
            accountNumber=account.account_number,
            customerId=account.customer_id,
            status=account.status,
            previousStatus=previous_status,
            reason=payload.reason,
        )

    def deposit(self, account_id: UUID, amount: Decimal) -> AccountRead:
        account = get_or_404(self._db, Account, account_id, "Account")
        account.balance += amount
        return AccountRead.model_validate(commit_refresh(self._db, account))

    def withdraw(self, account_id: UUID, amount: Decimal) -> AccountRead:
        account = get_or_404(self._db, Account, account_id, "Account")
        account.balance -= amount
        return AccountRead.model_validate(commit_refresh(self._db, account))

    def get_all_accounts(self) -> list[AccountRead]:
        rows = self._db.scalars(select(Account).order_by(Account.opened_at.desc())).all()
        return [AccountRead.model_validate(row) for row in rows]
