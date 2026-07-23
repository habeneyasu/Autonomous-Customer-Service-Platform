from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Autonomous Customer Service Platform"
    app_env: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    secret_key: str = Field(..., min_length=16)

    # Database
    database_url: str = Field(..., description="SQLAlchemy database URL")
    database_echo: bool = False

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # MCP
    mcp_server_url: str = "http://localhost:8001"
    mcp_max_invocations: int = Field(default=10, ge=1, le=50)

    # LLM (OpenAI-compatible chat completions)
    llm_api_key: str | None = None
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    llm_timeout_seconds: float = Field(default=30.0, gt=0)
    llm_max_tool_rounds: int = Field(default=5, ge=1, le=10)

    # Knowledge / RAG
    knowledge_index_dir: str = ".knowledge/chroma"

    # Domain
    default_currency: str = "ETB"
    otp_ttl_seconds: int = Field(default=300, ge=60)
    otp_max_attempts: int = Field(default=3, ge=1)
    idempotency_ttl_seconds: int = Field(default=86400, ge=60)

    # Rate limiting
    rate_limit_requests: int = Field(default=100, ge=1)
    rate_limit_window_seconds: int = Field(default=60, ge=1)

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
