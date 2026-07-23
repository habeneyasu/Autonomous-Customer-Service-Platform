from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from services.base import commit_refresh, get_or_404, require_owned_account, verify_customer_otp
from shared.constants.limits import (
    DEFAULT_TRANSACTION_HISTORY_LIMIT,
    MAX_TRANSACTION_HISTORY_LIMIT,
    REFERENCE_NUMBER_PREFIX,
)
from shared.constants.otp import OTP_PURPOSE_TRANSFER_VERIFICATION
from shared.enum.account_status import AccountStatus
from shared.enum.transaction_status import TransactionStatus
from shared.enum.transaction_type import TransactionType
from shared.exceptions.domain import InsufficientFundsError, NotFoundError, ValidationError
from shared.models.account import Account
from shared.models.customer import Customer
from shared.models.transaction import Transaction
from shared.schemas.transaction import (
    ExecuteP2PTransferRequest,
    TransactionCreate,
    TransactionHistoryResponse,
    TransactionRead,
    TransferRequest,
)


class TransactionService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, payload: TransactionCreate) -> TransactionRead:
        transaction = commit_refresh(self._db, Transaction(**payload.model_dump()))
        return TransactionRead.model_validate(transaction)

    def transfer(self, payload: TransferRequest) -> TransactionRead:
        if payload.sender_account_id == payload.receiver_account_id:
            raise ValidationError("Sender and receiver accounts must be different")

        sender, receiver = self._lock_accounts(
            payload.sender_account_id,
            payload.receiver_account_id,
        )
        self._validate_transfer(sender, receiver, payload.amount, payload.currency)

        sender.balance -= payload.amount
        receiver.balance += payload.amount

        transaction = Transaction(
            correlation_id=payload.correlation_id or uuid4(),
            sender_account_id=sender.account_id,
            receiver_account_id=receiver.account_id,
            amount=payload.amount,
            currency=payload.currency,
            transaction_type=TransactionType.TRANSFER,
            reference_number=self._next_reference_number(),
            status=TransactionStatus.COMMITTED,
            executed_at=datetime.now(UTC),
        )
        self._db.add(sender)
        self._db.add(receiver)
        return TransactionRead.model_validate(commit_refresh(self._db, transaction))

    def execute_p2p_transfer(
        self,
        customer_id: UUID,
        payload: ExecuteP2PTransferRequest,
    ) -> TransactionRead:
        verify_customer_otp(
            self._db,
            customer_id=customer_id,
            otp_code=payload.otp_code,
            purpose=OTP_PURPOSE_TRANSFER_VERIFICATION,
            correlation_id=payload.correlation_id,
        )
        require_owned_account(self._db, payload.sender_account_id, customer_id)
        return self.transfer(payload.to_transfer_request())

    def get(self, transaction_id: UUID) -> TransactionRead:
        return TransactionRead.model_validate(
            get_or_404(self._db, Transaction, transaction_id, "Transaction")
        )

    def get_transaction_history_by_customer_id(
        self,
        customer_id: UUID,
        *,
        limit: int = DEFAULT_TRANSACTION_HISTORY_LIMIT,
        offset: int = 0,
    ) -> TransactionHistoryResponse:
        if limit < 1 or limit > MAX_TRANSACTION_HISTORY_LIMIT:
            raise ValidationError(
                f"limit must be between 1 and {MAX_TRANSACTION_HISTORY_LIMIT}"
            )
        if offset < 0:
            raise ValidationError("offset must be >= 0")

        get_or_404(self._db, Customer, customer_id, "Customer")
        account_ids = list(
            self._db.scalars(select(Account.account_id).where(Account.customer_id == customer_id))
        )
        if not account_ids:
            return TransactionHistoryResponse(
                customerId=customer_id,
                transactions=[],
                totalReturned=0,
                limit=limit,
                offset=offset,
            )

        rows = self._db.scalars(
            select(Transaction)
            .where(
                or_(
                    Transaction.sender_account_id.in_(account_ids),
                    Transaction.receiver_account_id.in_(account_ids),
                )
            )
            .order_by(Transaction.created_at.desc())
            .limit(limit)
            .offset(offset)
        ).all()
        transactions = [TransactionRead.model_validate(row) for row in rows]
        return TransactionHistoryResponse(
            customerId=customer_id,
            transactions=transactions,
            totalReturned=len(transactions),
            limit=limit,
            offset=offset,
        )

    def _lock_accounts(self, sender_id: UUID, receiver_id: UUID) -> tuple[Account, Account]:
        first_id, second_id = sorted((sender_id, receiver_id), key=str)
        first = self._db.scalar(
            select(Account).where(Account.account_id == first_id).with_for_update()
        )
        second = self._db.scalar(
            select(Account).where(Account.account_id == second_id).with_for_update()
        )
        if first is None:
            raise NotFoundError(f"Account {first_id} not found")
        if second is None:
            raise NotFoundError(f"Account {second_id} not found")
        accounts = {first.account_id: first, second.account_id: second}
        return accounts[sender_id], accounts[receiver_id]

    def _validate_transfer(
        self,
        sender: Account,
        receiver: Account,
        amount: Decimal,
        currency: str,
    ) -> None:
        if sender.status != AccountStatus.ACTIVE:
            raise ValidationError("Sender account is not active")
        if receiver.status != AccountStatus.ACTIVE:
            raise ValidationError("Receiver account is not active")
        if sender.currency != currency or receiver.currency != currency:
            raise ValidationError("Currency mismatch between accounts and transfer request")
        if sender.balance < amount:
            raise InsufficientFundsError("Insufficient funds")

    def _next_reference_number(self) -> str:
        return f"{REFERENCE_NUMBER_PREFIX}{uuid4().hex[:12].upper()}"
