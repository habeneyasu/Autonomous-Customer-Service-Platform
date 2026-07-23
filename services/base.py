from typing import TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.orm import Session

from shared.exceptions.domain import ForbiddenError, NotFoundError
from shared.models.account import Account
from shared.schemas.otp_api import OtpVerifyRequest

T = TypeVar("T")


def get_or_404(db: Session, model: type[T], entity_id: UUID, label: str) -> T:
    row = db.get(model, entity_id)
    if row is None:
        raise NotFoundError(f"{label} {entity_id} not found")
    return row


def apply_updates(instance: object, payload: BaseModel) -> None:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(instance, field, value)


def commit_refresh(db: Session, instance: T) -> T:
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return instance


def require_owned_account(db: Session, account_id: UUID, customer_id: UUID) -> Account:
    account = get_or_404(db, Account, account_id, "Account")
    if account.customer_id != customer_id:
        raise ForbiddenError("Account does not belong to the authenticated customer")
    return account


def verify_customer_otp(
    db: Session,
    *,
    customer_id: UUID,
    otp_code: str,
    purpose: str,
    correlation_id: UUID | None = None,
) -> None:
    from services.otp_service import OtpService

    OtpService(db).verify(
        OtpVerifyRequest(
            customer_id=customer_id,
            otp_code=otp_code,
            purpose=purpose,
            correlation_id=correlation_id,
        )
    )
