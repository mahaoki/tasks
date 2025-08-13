from __future__ import annotations

import os
import sys
from collections.abc import AsyncIterator
from pathlib import Path

import asyncpg
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


class DummyUserClient:
    async def verify_users(self, user_ids):  # pragma: no cover - simple stub
        return None

    async def get_sector_name(self, sector_id):  # pragma: no cover - simple stub
        return "Sector"


@pytest_asyncio.fixture()
async def session(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[AsyncSession]:
    database_url = os.getenv(
        "TEST_TASKS_DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/test",
    )
    monkeypatch.setenv("TASKS_DATABASE_URL", database_url)

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from app.core.database import Base
    sys.path.pop(0)

    pool = await asyncpg.create_pool(database_url.replace("+asyncpg", ""))
    async with pool.acquire() as conn:
        await conn.execute("CREATE SCHEMA IF NOT EXISTS tasks")

    engine = create_async_engine(database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with async_session() as sess:
            yield sess
    finally:
        await engine.dispose()
        await pool.close()


@pytest_asyncio.fixture()
async def client(session: AsyncSession) -> AsyncIterator[tuple[AsyncClient, AsyncSession]]:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from app.api.tasks import get_task_service
    from app.core.database import get_session
    from app.main import app
    from app.services.tasks import TaskService
    sys.path.pop(0)

    async def override_get_session() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_task_service] = lambda: TaskService(
        user_client=DummyUserClient()
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac, session
    app.dependency_overrides.clear()

