from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from services.base import apply_updates, get_or_404
from shared.exceptions.domain import NotFoundError
from shared.models.address import Address
from shared.schemas.address import AddressCreate, AddressRead, AddressUpdate


class AddressService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, payload: AddressCreate) -> AddressRead:
        address = Address(**payload.model_dump())
        self._db.add(address)
        self._db.commit()
        self._db.refresh(address)
        return AddressRead.model_validate(address)

    def get(self, address_id: UUID) -> AddressRead:
        return AddressRead.model_validate(get_or_404(self._db, Address, address_id, "Address"))

    def update(self, address_id: UUID, payload: AddressUpdate) -> AddressRead:
        address = get_or_404(self._db, Address, address_id, "Address")
        apply_updates(address, payload)
        self._db.commit()
        self._db.refresh(address)
        return AddressRead.model_validate(address)

    def delete(self, address_id: UUID) -> None:
        self._db.delete(get_or_404(self._db, Address, address_id, "Address"))
        self._db.commit()

    def list_addresses(self) -> list[AddressRead]:
        rows = self._db.scalars(select(Address)).all()
        return [AddressRead.model_validate(row) for row in rows]
