from __future__ import annotations

import sys
from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.domain.schemas import (  # noqa: E402
    ErrorResponse,
    ProjectCreate,
    TaskCreate,
    TaskListResponse,
)
from app.repositories import ProjectRepository  # noqa: E402
from app.services.tasks import TaskService  # noqa: E402

sys.path.pop(0)


class DummyUserClient:
    async def verify_users(self, user_ids):  # pragma: no cover - simple stub
        return None

    async def get_sector_name(self, sector_id):  # pragma: no cover - simple stub
        return "Sector"


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
