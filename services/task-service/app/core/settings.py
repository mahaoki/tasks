# isort: skip_file
from __future__ import annotations

from typing import List

from pydantic import AnyUrl, AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    tasks_database_url: AnyUrl = Field(
        "sqlite+aiosqlite:///./tasks.db", alias="TASKS_DATABASE_URL"
    )
    auth_jwks_url: AnyHttpUrl = Field(
        "http://auth-service/jwks.json", alias="AUTH_JWKS_URL"
    )
    user_service_base_url: AnyHttpUrl = Field(
        "http://user-service", alias="USER_SERVICE_BASE_URL"
    )
    cors_allowed_origins: List[str] = Field(["*"], alias="CORS_ALLOWED_ORIGINS")
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    pagination_default: int = Field(50, alias="PAGINATION_DEFAULT")
    pagination_max: int = Field(100, alias="PAGINATION_MAX")
    service_name: str = Field("task-service", alias="SERVICE_NAME")
    enable_metrics: bool = Field(False, alias="ENABLE_METRICS")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        populate_by_name=True,
        extra="forbid",
    )

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def split_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v


settings = Settings()  # type: ignore[call-arg]
