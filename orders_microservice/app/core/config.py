from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    database_url: str = Field(..., description="Async SQLAlchemy DB URL")
    test_database_url: str | None = Field(
        default=None, description="DB URL for tests"
    )
    products_base_url: str = Field(
        ..., description="Products microservice base URL"
    )
    products_request_timeout_s: float = Field(
        default=2.0, description="HTTP request timeout (seconds) for Products calls"
    )
    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
