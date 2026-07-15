import hashlib


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def hash_idempotency_key(idempotency_key: str, endpoint: str) -> str:
    return sha256_hex(f"{idempotency_key}:{endpoint}")
