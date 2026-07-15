from contextvars import ContextVar, Token

correlation_id_var: ContextVar[str | None] = ContextVar("correlation_id", default=None)


def get_correlation_id() -> str | None:
    return correlation_id_var.get()


def set_correlation_id(correlation_id: str | None) -> Token[str | None]:
    """Set the correlation id and return a token for resetting the context."""
    return correlation_id_var.set(correlation_id)


def reset_correlation_id(token: Token[str | None]) -> None:
    """Reset correlation id to its previous value using the token."""
    correlation_id_var.reset(token)
