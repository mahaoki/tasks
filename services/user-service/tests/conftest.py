from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

import asyncpg
import jwt
import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient


@pytest_asyncio.fixture(scope="function")
async def client(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[AsyncClient]:
    database_url = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/test",
    )
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("JWT_SECRET_KEY", "secret")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("SMTP_HOST", "smtp")
    monkeypatch.setenv("SMTP_PORT", "25")
    monkeypatch.setenv("SMTP_USER", "user")
    monkeypatch.setenv("SMTP_PASSWORD", "pass")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", '["*"]')

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    for key in list(sys.modules):
        if key.startswith("app"):
            sys.modules.pop(key, None)
    from app.database import Base, async_engine  # noqa: E402
    from app.main import app  # noqa: E402

    pool = await asyncpg.create_pool(database_url.replace("+asyncpg", ""))
    async with pool.acquire() as conn:
        await conn.execute("CREATE SCHEMA IF NOT EXISTS users")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await app.router.startup()
        try:
            yield
        finally:
            await app.router.shutdown()

    async with lifespan(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    await pool.close()


def create_token(user_id: str, roles: list[str]) -> str:
    from app.settings import get_settings

    settings = get_settings()
    payload = {"sub": user_id, "roles": roles}
    return jwt.encode(
        payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
