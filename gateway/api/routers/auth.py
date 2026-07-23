from fastapi import APIRouter, status

from gateway.api.dependencies import SessionDep
from services.auth_service import AuthService
from shared.schemas.auth import (
    CustomerRegister,
    LoginRequest,
    LoginResponse,
    SessionBootstrapRequest,
    SessionBootstrapResponse,
)
from shared.schemas.customer import CustomerRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
def register(payload: CustomerRegister, db: SessionDep) -> CustomerRead:
    return AuthService(db).register(payload)


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: SessionDep) -> LoginResponse:
    return AuthService(db).login(payload)


@router.post("/session", response_model=SessionBootstrapResponse)
def bootstrap_session(payload: SessionBootstrapRequest, db: SessionDep) -> SessionBootstrapResponse:
    return AuthService(db).bootstrap_session(payload)
