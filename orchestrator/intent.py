"""Lightweight intent hint for the prototype (replace with LLM classifier later)."""

from __future__ import annotations


def infer_intent(text: str) -> str:
    lowered = text.lower()
    if any(word in lowered for word in ("freeze", "lock account", "block account")):
        return "ACCOUNT_MANAGEMENT"
    if any(word in lowered for word in ("transfer", "send money", "p2p")):
        return "FUND_TRANSFER"
    if any(word in lowered for word in ("history", "transactions", "statement")):
        return "TRANSACTION_HISTORY"
    if any(word in lowered for word in ("balance", "how much")):
        return "BALANCE_INQUIRY"
    return "GENERAL_INQUIRY"
