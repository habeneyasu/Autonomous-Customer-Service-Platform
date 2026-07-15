from enum import Enum


class AccountType(str, Enum):
    SAVINGS = "SAVINGS"
    CHECKING = "CHECKING"
    LOAN = "LOAN"
