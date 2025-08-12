from __future__ import annotations

import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

os.environ["TASKS_DATABASE_URL"] = "sqlite+aiosqlite://"

from task_service.api.tasks import get_task_service  # noqa: E402
from task_service.core.database import Base, get_session  # noqa: E402
from task_service.domain.schemas import (  # noqa: E402
    ErrorResponse,
    ProjectCreate,
    TaskCreate,
    TaskListResponse,
)
from task_service.main import app  # noqa: E402
from task_service.repositories import ProjectRepository  # noqa: E402
from task_service.services.tasks import TaskService  # noqa: E402


class DummyUserClient:
    async def verify_users(self, user_ids):  # pragma: no cover - simple stub
        return None

    async def get_sector_name(self, sector_id):  # pragma: no cover - simple stub
        return "Sector"


@pytest_asyncio.fixture()
async def client() -> AsyncIterator[tuple[AsyncClient, AsyncSession]]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.exec_driver_sql("ATTACH DATABASE ':memory:' AS tasks")
        await conn.run_sync(Base.metadata.create_all)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:

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
    await engine.dispose()


@pytest.mark.asyncio()
async def test_list_tasks_pagination(client: tuple[AsyncClient, AsyncSession]) -> None:
    ac, session = client
    project_repo = ProjectRepository()
    project = await project_repo.create(session, ProjectCreate(name="p", slug="p"))
    service = TaskService(user_client=DummyUserClient())
    await service.create(session, TaskCreate(project_id=project.id, title="t1"))
    await service.create(session, TaskCreate(project_id=project.id, title="t2"))
    resp = await ac.get(f"/tasks/projects/{project.id}/tasks?offset=0&limit=1")
    assert resp.status_code == 200
    body = TaskListResponse.model_validate(resp.json())
    assert body.pagination.total == 2
    assert len(body.tasks) == 1


@pytest.mark.asyncio()
async def test_get_task_not_found(client: tuple[AsyncClient, AsyncSession]) -> None:
    ac, _ = client
    resp = await ac.get("/tasks/tasks/999")
    assert resp.status_code == 404
    error = ErrorResponse.model_validate(resp.json()["detail"])
    assert error.code == "TASK_NOT_FOUND"
