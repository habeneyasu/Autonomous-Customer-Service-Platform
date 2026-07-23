import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from services.base import get_or_404
from shared.config.settings import get_settings
from shared.enum.otp_status import OtpStatus
from shared.exceptions.domain import OtpError
from shared.models.customer import Customer
from shared.models.one_time_password import OneTimePassword
from shared.schemas.one_time_password import OneTimePasswordRead
from shared.schemas.otp_api import OtpSendRequest, OtpSendResponse, OtpVerifyRequest, OtpVerifyResponse
from shared.utils.hashing import sha256_hex

_settings = get_settings()


class OtpService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def send(self, payload: OtpSendRequest) -> OtpSendResponse:
        get_or_404(self._db, Customer, payload.customer_id, "Customer")

        self._expire_pending(payload.customer_id, payload.purpose)
        code = f"{secrets.randbelow(10**6):06d}"
        otp = OneTimePassword(
            customer_id=payload.customer_id,
            otp_code_hash=sha256_hex(code),
            purpose=payload.purpose,
            status=OtpStatus.PENDING,
            expires_at=datetime.now(UTC) + timedelta(seconds=_settings.otp_ttl_seconds),
        )
        self._db.add(otp)
        self._db.commit()
        self._db.refresh(otp)
        return OtpSendResponse(
            otp_id=otp.otp_id,
            customer_id=otp.customer_id,
            purpose=otp.purpose,
            status=otp.status,
            expires_at=otp.expires_at,
            attempts_remaining=_settings.otp_max_attempts,
            dev_otp_code=code if not _settings.is_production else None,
        )

    def verify(self, payload: OtpVerifyRequest) -> OtpVerifyResponse:
        otp = self._db.scalar(
            select(OneTimePassword)
            .where(
                OneTimePassword.customer_id == payload.customer_id,
                OneTimePassword.purpose == payload.purpose,
                OneTimePassword.status == OtpStatus.PENDING,
            )
            .order_by(OneTimePassword.created_at.desc())
        )
        if otp is None:
            raise OtpError("No pending OTP found")

        now = datetime.now(UTC)
        if otp.expires_at <= now:
            otp.status = OtpStatus.EXPIRED
            self._db.commit()
            raise OtpError("OTP has expired")

        if sha256_hex(payload.otp_code) != otp.otp_code_hash:
            otp.attempts += 1
            if otp.attempts >= _settings.otp_max_attempts:
                otp.status = OtpStatus.FAILED
            self._db.commit()
            remaining = max(0, _settings.otp_max_attempts - otp.attempts)
            raise OtpError(f"Invalid OTP. Attempts remaining: {remaining}")

        otp.status = OtpStatus.VERIFIED
        self._db.commit()
        return OtpVerifyResponse(
            otp_id=otp.otp_id,
            customer_id=otp.customer_id,
            status=otp.status,
            attempts_remaining=max(0, _settings.otp_max_attempts - otp.attempts),
            verified_at=now,
        )

    def get(self, otp_id: UUID) -> OneTimePasswordRead:
        return OneTimePasswordRead.model_validate(
            get_or_404(self._db, OneTimePassword, otp_id, "OTP record")
        )

    def list_by_customer(
        self,
        customer_id: UUID,
        *,
        purpose: str | None = None,
        limit: int = 20,
    ) -> list[OneTimePasswordRead]:
        get_or_404(self._db, Customer, customer_id, "Customer")

        stmt = select(OneTimePassword).where(OneTimePassword.customer_id == customer_id)
        if purpose:
            stmt = stmt.where(OneTimePassword.purpose == purpose)
        rows = self._db.scalars(stmt.order_by(OneTimePassword.created_at.desc()).limit(limit)).all()
        return [OneTimePasswordRead.model_validate(row) for row in rows]

    def _expire_pending(self, customer_id: UUID, purpose: str) -> None:
        for otp in self._db.scalars(
            select(OneTimePassword).where(
                OneTimePassword.customer_id == customer_id,
                OneTimePassword.purpose == purpose,
                OneTimePassword.status == OtpStatus.PENDING,
            )
        ).all():
            otp.status = OtpStatus.EXPIRED
        self._db.flush()
