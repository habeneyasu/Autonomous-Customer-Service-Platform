from uuid import UUID

from fastapi import APIRouter, Query

from gateway.api.dependencies import SessionDep
from services.otp_service import OtpService
from shared.schemas.one_time_password import OneTimePasswordRead
from shared.schemas.otp_api import OtpSendRequest, OtpSendResponse, OtpVerifyRequest, OtpVerifyResponse

router = APIRouter(prefix="/otp", tags=["otp"])


@router.post("/send", response_model=OtpSendResponse)
def send_otp(payload: OtpSendRequest, db: SessionDep) -> OtpSendResponse:
    return OtpService(db).send(payload)


@router.post("/verify", response_model=OtpVerifyResponse)
def verify_otp(payload: OtpVerifyRequest, db: SessionDep) -> OtpVerifyResponse:
    return OtpService(db).verify(payload)


@router.get("/customers/{customer_id}", response_model=list[OneTimePasswordRead])
def list_customer_otps(
    customer_id: UUID,
    db: SessionDep,
    purpose: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[OneTimePasswordRead]:
    return OtpService(db).list_by_customer(customer_id, purpose=purpose, limit=limit)


@router.get("/{otp_id}", response_model=OneTimePasswordRead)
def get_otp_record(otp_id: UUID, db: SessionDep) -> OneTimePasswordRead:
    return OtpService(db).get(otp_id)
