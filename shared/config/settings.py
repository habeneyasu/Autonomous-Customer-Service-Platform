from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = "Autonomous Customer Service Platform"
    app_env: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    secret_key: str = "change-me-in-production"

    # Database
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/acsp"
    database_echo: bool = False

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # MCP
    mcp_server_url: str = "http://localhost:8001"

    # Domain
    default_currency: str = "ETB"
    otp_ttl_seconds: int = 300
    otp_max_attempts: int = 3
    idempotency_ttl_seconds: int = 86400

    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
