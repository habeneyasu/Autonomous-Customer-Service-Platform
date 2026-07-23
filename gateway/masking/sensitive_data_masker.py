"""Scrub sensitive customer and financial data from log output.

Masking rules (customer input → log; platform output noted):

  1. PIN                      full: ****
  2. Password                  full: ******
  3. OTP                       full: ******
  4. Card number (PAN)         partial: 4111********1111
  5. CVV / CVC                 full: ***
  6. Card expiry               full: **/**
  7. Account number            partial: 1000******67
  8. Beneficiary account       partial: 9876******10
  9. National ID               full: ****
 10. Passport                  full: ****
 11. TIN                       full: ****
 12. Phone number              partial: +251***...***
 13. Date of birth             full: **/**/****
 14. Bill reference            partial: BILL****
 15. Transaction amount        chat: shown; logs: [MASKED_AMOUNT]
 16. Account balance           chat: shown; logs: [MASKED_AMOUNT]
 17. Transaction reference     chat: shown; logs: kept for correlation
"""

from __future__ import annotations

import logging
import re
from collections.abc import Callable
from dataclasses import dataclass
from re import Pattern

# Fixed masks per compliance specification.
MASK_PIN = "****"
MASK_PASSWORD = "******"
MASK_OTP = "******"
MASK_CVV = "***"
MASK_EXPIRY = "**/**"
MASK_GOV_ID = "****"
MASK_DOB = "**/**/****"
MASK_AMOUNT = "[MASKED_AMOUNT]"

_LABEL = r"(?P<label>{labels})\b\s*[:=]\s*[\"']?(?P<value>[^\"'\s,;]+)[\"']?"


def _label_rule(labels: str, mask: str) -> tuple[Pattern[str], Callable[[re.Match[str]], str]]:
    pattern = re.compile(_LABEL.format(labels=labels), re.IGNORECASE)

    def repl(match: re.Match[str]) -> str:
        return f"{match.group('label')}: {mask}"

    return pattern, repl


@dataclass(frozen=True)
class _PatternRule:
    name: str
    pattern: Pattern[str]
    repl: str | Callable[[re.Match[str]], str]


def _mask_account(match: re.Match[str]) -> str:
    prefix = match.group(1) or ""
    return f"{prefix}{match.group(2)}******{match.group(3)}"


def _mask_phone(match: re.Match[str]) -> str:
    return f"{match.group(1)}***...***"


def _build_rules(*, for_log: bool) -> list[_PatternRule]:
    rules: list[_PatternRule] = [
        _PatternRule("pin", *_label_rule("pin", MASK_PIN)),
        _PatternRule("password", *_label_rule("password|pass", MASK_PASSWORD)),
        _PatternRule("otp", *_label_rule("otp|one[-_ ]?time[-_ ]?password|verification[-_ ]?code", MASK_OTP)),
        _PatternRule("cvv", *_label_rule("cvv|cvc", MASK_CVV)),
        _PatternRule(
            "card_expiry",
            *_label_rule("expiry|exp_date|expiration", MASK_EXPIRY),
        ),
        _PatternRule(
            "gov_id",
            *_label_rule("national_id|passport|tin|id_number", MASK_GOV_ID),
        ),
        _PatternRule("dob", *_label_rule("dob|birth_date|date_of_birth", MASK_DOB)),
        # PAN before account numbers to avoid overlapping digit sequences.
        _PatternRule(
            "pan",
            re.compile(r"\b(?P<first>\d{4})\d{8}(?P<last>\d{4})\b"),
            lambda m: f"{m.group('first')}********{m.group('last')}",
        ),
        _PatternRule(
            "account",
            re.compile(r"\b(?P<prefix>ACC-)?(?P<start>\d{4})\d{4,10}(?P<end>\d{2})\b"),
            _mask_account,
        ),
        _PatternRule(
            "phone",
            re.compile(r"(?P<prefix>\+251|0)(?P<carrier>[97])\d{8}\b"),
            _mask_phone,
        ),
        _PatternRule(
            "bill_reference",
            re.compile(r"(?i)\b(?P<prefix>BILL-?)[A-Z0-9]+\b"),
            r"\g<prefix>****",
        ),
    ]

    if for_log:
        rules.extend(
            [
                _PatternRule(
                    "amount_balance",
                    *_label_rule("amount|balance|ledger_balance", MASK_AMOUNT),
                ),
            ]
        )

    # Rule 17: transaction references are intentionally not masked.
    return rules


class SensitiveDataMasker(logging.Filter):
    """Logging filter that scrubs sensitive values from log messages."""

    def __init__(self) -> None:
        super().__init__()
        self._rules = _build_rules(for_log=True)

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self.mask(record.msg)
        if record.args:
            record.args = tuple(
                self.mask(arg) if isinstance(arg, str) else arg for arg in record.args
            )
        return True

    def mask(self, text: str, *, for_log: bool = True) -> str:
        """Apply all masking rules. Use ``for_log=False`` to keep amounts visible."""
        rules = self._rules if for_log else _build_rules(for_log=False)
        for rule in rules:
            if isinstance(rule.repl, str):
                text = rule.pattern.sub(rule.repl, text)
            else:
                text = rule.pattern.sub(rule.repl, text)
        return text


_masker = SensitiveDataMasker()


def mask_sensitive_data(text: str, *, for_log: bool = True) -> str:
    """Mask sensitive data in *text* (standalone helper)."""
    return _masker.mask(text, for_log=for_log)
