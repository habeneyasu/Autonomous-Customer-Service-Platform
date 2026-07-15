from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


def utc_now_naive() -> datetime:
    """Return current UTC time as naive datetime (for legacy compatibility)."""
    return datetime.utcnow()


def ensure_utc(dt: datetime) -> datetime:
    """Attach UTC timezone to a naive datetime; pass through aware datetimes."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt
