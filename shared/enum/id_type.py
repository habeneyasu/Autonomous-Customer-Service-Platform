from enum import Enum


class IdType(str, Enum):
    NATIONAL_ID = "NATIONAL_ID"
    PASSPORT = "PASSPORT"
    TIN = "TIN"
