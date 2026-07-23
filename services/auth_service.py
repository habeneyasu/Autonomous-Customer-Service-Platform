from datetime import UTC, datetime, timedelta
from typing import NamedTuple
from uuid import UUID

import secrets
from sqlalchemy import select
from sqlalchemy.orm import Session

from services.base import get_or_404
from shared.constants.limits import MAX_FAILED_LOGIN_ATTEMPTS
from shared.enum.customer_status import CustomerStatus
from shared.exceptions.domain import ConflictError, UnauthorizedError
from shared.models.address import Address
from shared.models.customer import Customer
from shared.models.user_auth import UserAuth
from shared.schemas.auth import (
    CustomerRegister,
    LoginRequest,
    LoginResponse,
    SessionBootstrapRequest,
    SessionBootstrapResponse,
)
from shared.schemas.customer import CustomerRead
from shared.utils.password import hash_password, verify_password

_SESSION_TTL = timedelta(hours=8)


class SessionRecord(NamedTuple):
    session_id: str
    customer_id: UUID
    expires_at: datetime


class AuthService:
    _sessions: dict[str, SessionRecord] = {}

    def __init__(self, db: Session) -> None:
        self._db = db

    def register(self, payload: CustomerRegister) -> CustomerRead:
        if self._db.scalar(select(UserAuth).where(UserAuth.username == payload.username)):
            raise ConflictError(f"Username {payload.username} is already taken")

        address_id = None
        if payload.region and payload.city:
            address = Address(
                region=payload.region,
                city=payload.city,
                street=payload.street,
                postal_code=payload.postal_code,
            )
            self._db.add(address)
            self._db.flush()
            address_id = address.address_id

        customer = Customer(
            first_name=payload.first_name,
            middle_name=payload.middle_name,
            last_name=payload.last_name,
            email=str(payload.email),
            phone_number=payload.phone_number,
            id_type=payload.id_type,
            id_number=payload.id_number,
            address_id=address_id,
            status=CustomerStatus.ACTIVE,
        )
        self._db.add(customer)
        self._db.flush()
        self._db.add(
            UserAuth(
                customer_id=customer.customer_id,
                username=payload.username,
                password_hash=hash_password(payload.password),
            )
        )
        self._db.commit()
        self._db.refresh(customer)
        return CustomerRead(
            customer_id=customer.customer_id,
            first_name=customer.first_name,
            middle_name=customer.middle_name,
            last_name=customer.last_name,
            email=customer.email,
            username=payload.username,
            phone_number=customer.phone_number,
            id_type=customer.id_type,
            id_number=customer.id_number,
            address_id=customer.address_id,
            status=customer.status,
            created_at=customer.created_at,
            updated_at=customer.updated_at,
        )

    def login(self, payload: LoginRequest) -> LoginResponse:
        user_auth = self._db.scalar(select(UserAuth).where(UserAuth.username == payload.username))
        if user_auth is None or not verify_password(payload.password, user_auth.password_hash):
            if user_auth:
                user_auth.failed_attempts += 1
                self._db.commit()
            raise UnauthorizedError("Invalid username or password")
        if user_auth.failed_attempts >= MAX_FAILED_LOGIN_ATTEMPTS:
            raise UnauthorizedError("Account locked due to failed login attempts")

        user_auth.failed_attempts = 0
        user_auth.last_login_at = datetime.now(UTC)
        self._db.commit()
        session = self._issue_session(user_auth.customer_id)
        return LoginResponse(
            customer_id=user_auth.customer_id,
            session_id=session.session_id,
            session_token=session.session_id,
            expires_at=session.expires_at,
        )

    def bootstrap_session(self, payload: SessionBootstrapRequest) -> SessionBootstrapResponse:
        customer = get_or_404(self._db, Customer, payload.customer_id, "Customer")
        session = self._issue_session(customer.customer_id)
        return SessionBootstrapResponse(
            session_id=session.session_id,
            session_token=session.session_id,
            customer_id=customer.customer_id,
            expires_at=session.expires_at,
        )

    def resolve_customer_id(self, session_token: str) -> UUID:
        session = self._sessions.get(session_token)
        if session is None or session.expires_at <= datetime.now(UTC):
            raise UnauthorizedError("Invalid or expired session token")
        return session.customer_id

    def _issue_session(self, customer_id: UUID) -> SessionRecord:
        session_id = secrets.token_urlsafe(32)
        record = SessionRecord(session_id, customer_id, datetime.now(UTC) + _SESSION_TTL)
        self._sessions[session_id] = record
        return record
