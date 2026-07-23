from uuid import UUID

from fastapi import APIRouter, Query, status

from gateway.api.dependencies import SessionDep
from services.customer_service import CustomerService
from shared.schemas.customer import CustomerCreate, CustomerRead, CustomerUpdate

router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
def create_customer(payload: CustomerCreate, db: SessionDep) -> CustomerRead:
    return CustomerService(db).create(payload)


@router.get("", response_model=list[CustomerRead])
def list_customers(
    db: SessionDep,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[CustomerRead]:
    return CustomerService(db).list_customers(limit=limit, offset=offset)


@router.get("/{customer_id}", response_model=CustomerRead)
def get_customer(customer_id: UUID, db: SessionDep) -> CustomerRead:
    return CustomerService(db).get(customer_id)


@router.patch("/{customer_id}", response_model=CustomerRead)
def update_customer(customer_id: UUID, payload: CustomerUpdate, db: SessionDep) -> CustomerRead:
    return CustomerService(db).update(customer_id, payload)
