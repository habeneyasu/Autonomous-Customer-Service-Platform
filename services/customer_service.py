from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from services.base import get_or_404
from shared.exceptions.domain import ConflictError, NotFoundError
from shared.models.customer import Customer
from shared.models.user_auth import UserAuth
from shared.schemas.customer import CustomerCreate, CustomerRead, CustomerUpdate
from shared.utils.password import hash_password


class CustomerService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, payload: CustomerCreate) -> CustomerRead:
        """Accept username/password at API level; persist profile then auth credentials."""
        self._ensure_unique(payload.email, payload.phone_number)
        if self._db.scalar(select(UserAuth).where(UserAuth.username == payload.username)):
            raise ConflictError(f"Username {payload.username} is already taken")

        customer = Customer(**payload.model_dump(exclude={"username", "password"}))
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
        return self._to_read(customer, payload.username)

    def get(self, customer_id: UUID) -> CustomerRead:
        return self._to_read(get_or_404(self._db, Customer, customer_id, "Customer"))

    def list_customers(self, *, limit: int = 50, offset: int = 0) -> list[CustomerRead]:
        rows = self._db.scalars(
            select(Customer).order_by(Customer.created_at.desc()).limit(limit).offset(offset)
        ).all()
        return [self._to_read(row) for row in rows]

    def update(self, customer_id: UUID, payload: CustomerUpdate) -> CustomerRead:
        customer = get_or_404(self._db, Customer, customer_id, "Customer")
        updates = payload.model_dump(exclude_unset=True, exclude={"username"})

        if "email" in updates and updates["email"] != customer.email:
            self._ensure_unique_email(updates["email"])
        if "phone_number" in updates and updates["phone_number"] != customer.phone_number:
            self._ensure_unique_phone(updates["phone_number"])

        for field, value in updates.items():
            setattr(customer, field, value)

        if payload.username is not None:
            user_auth = self._db.scalar(
                select(UserAuth).where(UserAuth.customer_id == customer_id)
            )
            if user_auth is None:
                raise NotFoundError("User auth not found for customer")
            if self._db.scalar(
                select(UserAuth).where(
                    UserAuth.username == payload.username,
                    UserAuth.customer_id != customer_id,
                )
            ):
                raise ConflictError(f"Username {payload.username} is already taken")
            user_auth.username = payload.username

        self._db.commit()
        self._db.refresh(customer)
        return self._to_read(customer)

    def _to_read(self, customer: Customer, username: str | None = None) -> CustomerRead:
        if username is None:
            user_auth = self._db.scalar(
                select(UserAuth).where(UserAuth.customer_id == customer.customer_id)
            )
            username = user_auth.username if user_auth else ""
        return CustomerRead(
            customer_id=customer.customer_id,
            first_name=customer.first_name,
            middle_name=customer.middle_name,
            last_name=customer.last_name,
            email=customer.email,
            username=username,
            phone_number=customer.phone_number,
            id_type=customer.id_type,
            id_number=customer.id_number,
            address_id=customer.address_id,
            status=customer.status,
            created_at=customer.created_at,
            updated_at=customer.updated_at,
        )

    def _ensure_unique(self, email: str, phone_number: str) -> None:
        self._ensure_unique_email(email)
        self._ensure_unique_phone(phone_number)

    def _ensure_unique_email(self, email: str) -> None:
        if self._db.scalar(select(Customer).where(Customer.email == email)):
            raise ConflictError(f"Email {email} is already registered")

    def _ensure_unique_phone(self, phone_number: str) -> None:
        if self._db.scalar(select(Customer).where(Customer.phone_number == phone_number)):
            raise ConflictError(f"Phone number {phone_number} is already registered")
