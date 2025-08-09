# isort: skip_file
from __future__ import annotations

from functools import lru_cache
from typing import List

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from pydantic import AnyUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _generate_keypair() -> tuple[str, str]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    pub_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return priv_pem, pub_pem


_DEFAULT_PRIVATE_KEY, _DEFAULT_PUBLIC_KEY = _generate_keypair()


class Settings(BaseSettings):
    database_url: AnyUrl = Field("sqlite:///./auth.db", alias="DATABASE_URL")
    jwt_private_key: str = Field(_DEFAULT_PRIVATE_KEY, alias="JWT_PRIVATE_KEY")
    jwt_public_key: str = Field(_DEFAULT_PUBLIC_KEY, alias="JWT_PUBLIC_KEY")
    jwt_algorithm: str = Field("RS256", alias="JWT_ALGORITHM")
    jwt_key_id: str = Field("local", alias="JWT_KEY_ID")
    access_token_expires_minutes: int = Field(15, alias="ACCESS_TOKEN_EXPIRES_MINUTES")
    refresh_token_expires_days: int = Field(7, alias="REFRESH_TOKEN_EXPIRES_DAYS")
    password_pepper: str | None = Field("", alias="PASSWORD_PEPPER")
    redis_url: str | None = Field(None, alias="REDIS_URL")
    cors_allow_origins: List[str] = Field(["*"], alias="CORS_ALLOW_ORIGINS")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        populate_by_name=True,
        extra="forbid",
    )

    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def split_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v


@lru_cache
def get_settings() -> Settings:
    """Return application settings, cached to avoid re-parsing."""
    return Settings()  # type: ignore[call-arg]
