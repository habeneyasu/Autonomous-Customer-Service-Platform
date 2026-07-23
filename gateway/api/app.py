from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from gateway.api.routers import accounts, addresses, auth, customers, otp, transactions
from shared.config.settings import get_settings
from shared.exceptions.base import AppError
from shared.exceptions.domain import (
    ConflictError,
    ForbiddenError,
    IdempotencyConflictError,
    InsufficientFundsError,
    NotFoundError,
    OtpError,
    RateLimitError,
    UnauthorizedError,
    ValidationError,
)
from shared.schemas.common import ErrorResponse, HealthResponse

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0", debug=settings.debug)

for router in (auth, customers, addresses, accounts, transactions, otp):
    app.include_router(router.router, prefix="/api/v1")


@app.get("/health", response_model=HealthResponse, tags=["health"])
def health() -> HealthResponse:
    return HealthResponse(app_name=settings.app_name, environment=settings.app_env)


def _json_error(code: str, message: str, status_code: int) -> JSONResponse:
    body = ErrorResponse(code=code, message=message).model_dump(mode="json")
    return JSONResponse(status_code=status_code, content=body)


def _register(app: FastAPI, exc_type: type[AppError], status_code: int) -> None:
    @app.exception_handler(exc_type)
    async def _handler(_: Request, exc: exc_type) -> JSONResponse:  # type: ignore[valid-type]
        return _json_error(exc.code, exc.message, status_code)


for error_type, code in (
    (NotFoundError, 404),
    (ConflictError, 409),
    (IdempotencyConflictError, 409),
    (ValidationError, 400),
    (UnauthorizedError, 401),
    (ForbiddenError, 403),
    (OtpError, 400),
    (InsufficientFundsError, 422),
    (RateLimitError, 429),
    (AppError, 500),
):
    _register(app, error_type, code)


@app.exception_handler(SQLAlchemyError)
async def database_error_handler(_: Request, exc: SQLAlchemyError) -> JSONResponse:
    message = str(getattr(exc, "orig", exc))
    if "failed to resolve host" in message.lower():
        message = "Invalid DATABASE_URL. URL-encode special characters in the password."
    return _json_error("database_error", message, 503)
