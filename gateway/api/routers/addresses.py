from uuid import UUID

from fastapi import APIRouter, status

from gateway.api.dependencies import SessionDep
from services.address_service import AddressService
from shared.schemas.address import AddressCreate, AddressRead, AddressUpdate

router = APIRouter(prefix="/addresses", tags=["addresses"])


@router.get("", response_model=list[AddressRead])
def list_addresses(db: SessionDep) -> list[AddressRead]:
    return AddressService(db).list_addresses()


@router.post("", response_model=AddressRead, status_code=status.HTTP_201_CREATED)
def create_address(payload: AddressCreate, db: SessionDep) -> AddressRead:
    return AddressService(db).create(payload)


@router.get("/{address_id}", response_model=AddressRead)
def get_address(address_id: UUID, db: SessionDep) -> AddressRead:
    return AddressService(db).get(address_id)


@router.patch("/{address_id}", response_model=AddressRead)
def update_address(address_id: UUID, payload: AddressUpdate, db: SessionDep) -> AddressRead:
    return AddressService(db).update(address_id, payload)


@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_address(address_id: UUID, db: SessionDep) -> None:
    AddressService(db).delete(address_id)
