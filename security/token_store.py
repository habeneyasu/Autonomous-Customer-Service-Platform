"""Session-scoped secure vault for tokenized sensitive values."""

from __future__ import annotations

import secrets
import threading
import time
from dataclasses import dataclass, field


@dataclass(frozen=True)
class TokenRecord:
    token: str
    value: str
    kind: str
    is_secret: bool = False


@dataclass
class SessionVault:
    session_id: str
    created_at: float = field(default_factory=time.time)
    records: dict[str, TokenRecord] = field(default_factory=dict)
    value_index: dict[tuple[str, str], str] = field(default_factory=dict)


class TokenStore:
    """In-memory vault keyed by session id (prototype; swap for Redis later)."""

    def __init__(self, *, ttl_seconds: int = 3600) -> None:
        self._ttl_seconds = ttl_seconds
        self._sessions: dict[str, SessionVault] = {}
        self._lock = threading.RLock()

    def create_session(self, session_id: str | None = None) -> str:
        sid = session_id or secrets.token_hex(8)
        with self._lock:
            self._purge_expired()
            self._sessions[sid] = SessionVault(session_id=sid)
        return sid

    def put(
        self,
        session_id: str,
        *,
        kind: str,
        value: str,
        is_secret: bool = False,
    ) -> str:
        """Store *value* and return a stable token for this session."""
        with self._lock:
            vault = self._require_vault(session_id)
            key = (kind, value)
            if key in vault.value_index:
                return vault.value_index[key]

            token = f"[{kind}_{secrets.token_hex(2).upper()}]"
            while token in vault.records:
                token = f"[{kind}_{secrets.token_hex(2).upper()}]"

            record = TokenRecord(
                token=token,
                value=value,
                kind=kind,
                is_secret=is_secret,
            )
            vault.records[token] = record
            vault.value_index[key] = token
            return token

    def get(self, session_id: str, token: str) -> TokenRecord | None:
        with self._lock:
            vault = self._sessions.get(session_id)
            if vault is None or self._is_expired(vault):
                return None
            return vault.records.get(token)

    def resolve(
        self,
        session_id: str,
        token: str,
        *,
        allow_secrets: bool = False,
    ) -> str | None:
        record = self.get(session_id, token)
        if record is None:
            return None
        if record.is_secret and not allow_secrets:
            return None
        return record.value

    def snapshot(self, session_id: str) -> dict[str, TokenRecord]:
        with self._lock:
            vault = self._sessions.get(session_id)
            if vault is None or self._is_expired(vault):
                return {}
            return dict(vault.records)

    def clear(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)

    def _require_vault(self, session_id: str) -> SessionVault:
        vault = self._sessions.get(session_id)
        if vault is None or self._is_expired(vault):
            vault = SessionVault(session_id=session_id)
            self._sessions[session_id] = vault
        return vault

    def _is_expired(self, vault: SessionVault) -> bool:
        return (time.time() - vault.created_at) > self._ttl_seconds

    def _purge_expired(self) -> None:
        expired = [
            sid for sid, vault in self._sessions.items() if self._is_expired(vault)
        ]
        for sid in expired:
            del self._sessions[sid]


_store: TokenStore | None = None


def get_token_store() -> TokenStore:
    global _store
    if _store is None:
        _store = TokenStore()
    return _store
