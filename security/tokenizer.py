"""Tokenize sensitive values in free text (Zone 2).

Raw values are stored in the session vault; LLM-facing text keeps placeholders.
Secrets (PIN/OTP/password/CVV) are redacted and never rehydrated into tool calls.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from re import Pattern

from security.token_store import TokenStore, get_token_store

# Matches tokens produced by this tokenizer, e.g. [ACC_A1B2]
TOKEN_PATTERN = re.compile(r"\[[A-Z]+_[0-9A-F]{4}\]")


@dataclass(frozen=True)
class _DetectRule:
    kind: str
    pattern: Pattern[str]
    is_secret: bool = False
    store: bool = True  # False => redact only, do not vault


# Order matters: PAN before account-like digit runs.
_DETECT_RULES: tuple[_DetectRule, ...] = (
    _DetectRule(
        "PIN",
        re.compile(
            r"(?i)\b(pin)\b\s*[:=]\s*[\"']?(?P<value>[a-zA-Z0-9$#@]{4,12})[\"']?"
        ),
        is_secret=True,
        store=False,
    ),
    _DetectRule(
        "PASS",
        re.compile(
            r"(?i)\b(password|pass)\b\s*[:=]\s*[\"']?(?P<value>\S+)[\"']?"
        ),
        is_secret=True,
        store=False,
    ),
    _DetectRule(
        "OTP",
        re.compile(
            r"(?i)\b(otp|verification[-_ ]?code)\b\s*[:=]\s*[\"']?(?P<value>\d{4,8})[\"']?"
        ),
        is_secret=True,
        store=False,
    ),
    _DetectRule(
        "CVV",
        re.compile(r"(?i)\b(cvv|cvc)\b\s*[:=]\s*[\"']?(?P<value>\d{3,4})[\"']?"),
        is_secret=True,
        store=False,
    ),
    _DetectRule(
        "PAN",
        re.compile(r"\b(?P<value>\d{4}\d{8}\d{4})\b"),
    ),
    _DetectRule(
        "ACC",
        re.compile(r"\b(?P<value>(?:ACC-)?\d{4}\d{4,10}\d{2})\b"),
    ),
    _DetectRule(
        "PHONE",
        re.compile(r"(?P<value>(?:\+251|0)[97]\d{8})\b"),
    ),
    _DetectRule(
        "BILL",
        re.compile(r"(?i)\b(?P<value>BILL-?[A-Z0-9]{4,})\b"),
    ),
    _DetectRule(
        "GOVID",
        re.compile(
            r"(?i)\b(national_id|passport|tin|id_number)\b\s*[:=]\s*[\"']?(?P<value>[a-zA-Z0-9\-]+)[\"']?"
        ),
    ),
    _DetectRule(
        "DOB",
        re.compile(
            r"(?i)\b(dob|birth_date|date_of_birth)\b\s*[:=]\s*[\"']?(?P<value>\d{2}/\d{2}/\d{4})[\"']?"
        ),
    ),
)


@dataclass
class TokenizeResult:
    session_id: str
    original_text: str
    tokenized_text: str
    tokens: dict[str, str] = field(default_factory=dict)


class Tokenizer:
    """Strip/replace sensitive spans and isolate raw values in the vault."""

    def __init__(self, store: TokenStore | None = None) -> None:
        self._store = store or get_token_store()

    def tokenize(self, text: str, *, session_id: str | None = None) -> TokenizeResult:
        sid = self._store.create_session(session_id)
        tokenized = text
        found: dict[str, str] = {}

        for rule in _DETECT_RULES:
            tokenized = self._apply_rule(sid, tokenized, rule, found)

        return TokenizeResult(
            session_id=sid,
            original_text=text,
            tokenized_text=tokenized,
            tokens=found,
        )

    def rehydrate(
        self,
        text: str,
        *,
        session_id: str,
        allow_secrets: bool = False,
    ) -> str:
        """Replace tokens with vault values (Zone 3)."""

        def repl(match: re.Match[str]) -> str:
            token = match.group(0)
            value = self._store.resolve(
                session_id,
                token,
                allow_secrets=allow_secrets,
            )
            return value if value is not None else token

        return TOKEN_PATTERN.sub(repl, text)

    def rehydrate_mapping(
        self,
        payload: dict,
        *,
        session_id: str,
        allow_secrets: bool = False,
    ) -> dict:
        """Deep-replace token strings inside a tool-argument mapping."""

        def walk(node):  # noqa: ANN001
            if isinstance(node, str):
                return self.rehydrate(
                    node,
                    session_id=session_id,
                    allow_secrets=allow_secrets,
                )
            if isinstance(node, list):
                return [walk(item) for item in node]
            if isinstance(node, dict):
                return {key: walk(value) for key, value in node.items()}
            return node

        return walk(payload)

    def _apply_rule(
        self,
        session_id: str,
        text: str,
        rule: _DetectRule,
        found: dict[str, str],
    ) -> str:
        def repl(match: re.Match[str]) -> str:
            value = match.group("value")
            if not rule.store:
                placeholder = f"[REDACTED_{rule.kind}]"
                return self._replace_span(match, placeholder)

            token = self._store.put(
                session_id,
                kind=rule.kind,
                value=value,
                is_secret=rule.is_secret,
            )
            found[token] = rule.kind
            return self._replace_span(match, token)

        return rule.pattern.sub(repl, text)

    @staticmethod
    def _replace_span(match: re.Match[str], replacement: str) -> str:
        """Keep label when present; otherwise replace the whole match."""
        if "value" in match.groupdict() and match.lastindex and match.lastindex > 1:
            label = match.group(1)
            return f"{label}: {replacement}"
        return replacement


def get_tokenizer() -> Tokenizer:
    return Tokenizer()
