from enum import Enum


class TransactionType(str, Enum):
    TRANSFER = "TRANSFER"
    BILL_PAYMENT = "BILL_PAYMENT"
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
