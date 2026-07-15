import uuid

from shared.constants.limits import ACCOUNT_NUMBER_PREFIX, REFERENCE_NUMBER_PREFIX


def new_uuid() -> uuid.UUID:
    return uuid.uuid4()


def build_account_number(sequence: int) -> str:
    return f"{ACCOUNT_NUMBER_PREFIX}{sequence:06d}"


def build_reference_number(sequence: int) -> str:
    return f"{REFERENCE_NUMBER_PREFIX}{sequence:010d}"
