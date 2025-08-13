from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Generator
from collections.abc import AsyncIterator

import asyncpg
import fakeredis
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


@pytest.fixture(scope="function")
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    pub_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    monkeypatch.setenv("JWT_PRIVATE_KEY", priv_pem.decode())
    monkeypatch.setenv("JWT_PUBLIC_KEY", pub_pem.decode())
    monkeypatch.setenv("JWT_ALGORITHM", "RS256")
    monkeypatch.setenv("JWT_KEY_ID", "test-key")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRES_MINUTES", "15")
    monkeypatch.setenv("REFRESH_TOKEN_EXPIRES_DAYS", "7")
    monkeypatch.setenv("PASSWORD_PEPPER", "")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "[\"*\"]")

    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from app.main import app  # noqa: E402
    from app import security  # noqa: E402
    from app.database import Base, engine  # noqa: E402

    security.redis_client = fakeredis.FakeRedis()  # type: ignore[assignment]
    Base.metadata.create_all(bind=engine)

    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="function")
async def async_client(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[AsyncClient]:
    database_url = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/test",
    )
    monkeypatch.setenv("DATABASE_URL", database_url)
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    pub_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    monkeypatch.setenv("JWT_PRIVATE_KEY", priv_pem.decode())
    monkeypatch.setenv("JWT_PUBLIC_KEY", pub_pem.decode())
    monkeypatch.setenv("JWT_ALGORITHM", "RS256")
    monkeypatch.setenv("JWT_KEY_ID", "test-key")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRES_MINUTES", "15")
    monkeypatch.setenv("REFRESH_TOKEN_EXPIRES_DAYS", "7")
    monkeypatch.setenv("PASSWORD_PEPPER", "")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "[\"*\"]")

    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from app.main import app  # noqa: E402
    from app import security  # noqa: E402
    from app.database import Base, async_engine  # noqa: E402

    security.redis_client = fakeredis.FakeAsyncRedis()  # type: ignore[assignment]

    pool = await asyncpg.create_pool(database_url.replace("+asyncpg", ""))
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    await pool.close()

