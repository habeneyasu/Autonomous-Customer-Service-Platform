from shared.exceptions.base import AppError


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, code="not_found")


class ConflictError(AppError):
    def __init__(self, message: str = "Resource conflict") -> None:
        super().__init__(message, code="conflict")


class ValidationError(AppError):
    def __init__(self, message: str = "Validation failed") -> None:
        super().__init__(message, code="validation_error")


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Unauthorized") -> None:
        super().__init__(message, code="unauthorized")


class ForbiddenError(AppError):
    def __init__(self, message: str = "Forbidden") -> None:
        super().__init__(message, code="forbidden")


class IdempotencyConflictError(AppError):
    def __init__(self, message: str = "Idempotency key conflict") -> None:
        super().__init__(message, code="idempotency_conflict")


class InsufficientFundsError(AppError):
    def __init__(self, message: str = "Insufficient funds") -> None:
        super().__init__(message, code="insufficient_funds")


class OtpError(AppError):
    def __init__(self, message: str = "OTP verification failed") -> None:
        super().__init__(message, code="otp_error")


class RateLimitError(AppError):
    def __init__(self, message: str = "Rate limit exceeded") -> None:
        super().__init__(message, code="rate_limit_exceeded")


class ExternalServiceError(AppError):
    def __init__(self, message: str = "External service error") -> None:
        super().__init__(message, code="external_service_error")
