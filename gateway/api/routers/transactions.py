from uuid import UUID

from fastapi import APIRouter, Query, status

from gateway.api.dependencies import SessionDep
from services.transaction_service import TransactionService
from shared.constants.limits import (
    DEFAULT_TRANSACTION_HISTORY_LIMIT,
    MAX_TRANSACTION_HISTORY_LIMIT,
)
from shared.schemas.transaction import (
    ExecuteP2PTransferRequest,
    TransactionHistoryResponse,
    TransactionRead,
    TransferRequest,
)

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("/transfer", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def transfer_balance(payload: TransferRequest, db: SessionDep) -> TransactionRead:
    return TransactionService(db).transfer(payload)


@router.post("/p2p", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def execute_p2p_transfer(
    payload: ExecuteP2PTransferRequest,
    db: SessionDep,
    customer_id: UUID,
) -> TransactionRead:
    """OTP-gated peer-to-peer transfer for the authenticated customer."""
    return TransactionService(db).execute_p2p_transfer(customer_id, payload)


@router.get("/customers/{customer_id}", response_model=TransactionHistoryResponse)
def list_customer_transactions(
    customer_id: UUID,
    db: SessionDep,
    limit: int = Query(
        default=DEFAULT_TRANSACTION_HISTORY_LIMIT,
        ge=1,
        le=MAX_TRANSACTION_HISTORY_LIMIT,
    ),
    offset: int = Query(default=0, ge=0),
) -> TransactionHistoryResponse:
    return TransactionService(db).get_transaction_history_by_customer_id(
        customer_id,
        limit=limit,
        offset=offset,
    )


@router.get("/{transaction_id}", response_model=TransactionRead)
def get_transaction(transaction_id: UUID, db: SessionDep) -> TransactionRead:
    return TransactionService(db).get(transaction_id)
