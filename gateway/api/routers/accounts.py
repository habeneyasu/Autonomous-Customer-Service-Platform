from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, status

from gateway.api.dependencies import SessionDep
from services.account_service import AccountService
from shared.schemas.account import (
    AccountCreate,
    AccountRead,
    AccountUpdate,
    FreezeAccountRequest,
    FreezeAccountResponse,
)
from shared.schemas.balance import CustomerBalanceResponse

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("/customers/{customer_id}", response_model=list[AccountRead])
def list_customer_accounts(customer_id: UUID, db: SessionDep) -> list[AccountRead]:
    return AccountService(db).list_by_customer(customer_id)


@router.get("/customers/{customer_id}/balance", response_model=CustomerBalanceResponse)
def get_customer_balance(customer_id: UUID, db: SessionDep) -> CustomerBalanceResponse:
    return AccountService(db).get_balance_by_customer(customer_id)


@router.post("", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def create_account(payload: AccountCreate, db: SessionDep) -> AccountRead:
    return AccountService(db).create(payload)


@router.get("/{account_id}", response_model=AccountRead)
def get_account(account_id: UUID, db: SessionDep) -> AccountRead:
    return AccountService(db).get(account_id)


@router.patch("/{account_id}", response_model=AccountRead)
def update_account(account_id: UUID, payload: AccountUpdate, db: SessionDep) -> AccountRead:
    return AccountService(db).update(account_id, payload)


@router.post("/{account_id}/freeze", response_model=FreezeAccountResponse)
def freeze_account(
    account_id: UUID,
    payload: FreezeAccountRequest,
    db: SessionDep,
    customer_id: UUID,
) -> FreezeAccountResponse:
    """Freeze an account after OTP verification.

    ``customer_id`` is required as a query parameter until session auth is wired
    into the gateway for this route.
    """
    body = payload.model_copy(update={"account_id": account_id})
    return AccountService(db).freeze_account(customer_id, body)


@router.post("/{account_id}/deposit", response_model=AccountRead, status_code=status.HTTP_200_OK)
def deposit_account(account_id: UUID, amount: Decimal, db: SessionDep) -> AccountRead:
    return AccountService(db).deposit(account_id, amount)


@router.post("/{account_id}/withdraw", response_model=AccountRead, status_code=status.HTTP_200_OK)
def withdraw_account(account_id: UUID, amount: Decimal, db: SessionDep) -> AccountRead:
    return AccountService(db).withdraw(account_id, amount)

@router.get("", response_model=list[AccountRead])
def get_all_accounts(db: SessionDep) -> list[AccountRead]:
    return AccountService(db).get_all_accounts()