from __future__ import annotations

from datetime import datetime, timedelta

import pytest
import pytest_asyncio
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)

from task_service.core.database import Base
from task_service.domain.models import Task
from task_service.domain.schemas import ProjectCreate, Status, TaskCreate
from task_service.repositories import ProjectRepository
from task_service.services.tasks import TaskService


@pytest_asyncio.fixture()
async def session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.exec_driver_sql("ATTACH DATABASE ':memory:' AS tasks")
        await conn.run_sync(Base.metadata.create_all)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        yield session
    await engine.dispose()


class DummyUserClient:
    async def verify_users(self, user_ids) -> None:  # pragma: no cover - simple stub
        return None

    async def get_sector_name(
        self, sector_id: int
    ) -> str:  # pragma: no cover - simple stub
        return "Sector"


def test_validate_dates() -> None:
    now = datetime.utcnow()
    cases = [
        {"start_date": now, "due_date": now - timedelta(days=1)},
        {"completed_at": now, "status": Status.PENDING},
        {
            "start_date": now,
            "completed_at": now - timedelta(days=1),
            "status": Status.COMPLETED,
        },
        {"status": Status.COMPLETED},
    ]
    for data in cases:
        with pytest.raises(ValidationError):
            TaskCreate(project_id=1, title="t", **data)

    valid = TaskCreate(
        project_id=1,
        title="t",
        start_date=now - timedelta(days=1),
        due_date=now + timedelta(days=1),
        status=Status.COMPLETED,
        completed_at=now,
    )
    assert valid.completed_at == now


def test_calculate_timeliness_on_time() -> None:
    now = datetime.utcnow().replace(microsecond=0, second=0, minute=0, hour=0)
    task = Task(
        id=1,
        project_id=1,
        title="t",
        code="X",
        start_date=now - timedelta(days=1),
        due_date=now + timedelta(days=1),
        completed_at=now,
    )
    metrics = TaskService()._calculate_timeliness(task)
    assert metrics["timeliness"] == "on_time"
    assert metrics["days_total"] == 2
    assert metrics["days_elapsed"] == 1
    assert metrics["days_remaining"] == 1


def test_calculate_timeliness_late() -> None:
    now = datetime.utcnow().replace(microsecond=0, second=0, minute=0, hour=0)
    task = Task(
        id=1,
        project_id=1,
        title="t",
        code="X",
        start_date=now - timedelta(days=2),
        due_date=now - timedelta(days=1),
        completed_at=now,
    )
    metrics = TaskService()._calculate_timeliness(task)
    assert metrics["timeliness"] == "late"
    assert metrics["days_total"] == 1
    assert metrics["days_elapsed"] == 2
    assert metrics["days_remaining"] == -1


def test_calculate_timeliness_overdue() -> None:
    now = datetime.utcnow().replace(microsecond=0, second=0, minute=0, hour=0)
    task = Task(
        id=1,
        project_id=1,
        title="t",
        code="X",
        start_date=now - timedelta(days=2),
        due_date=now - timedelta(days=1),
    )
    metrics = TaskService()._calculate_timeliness(task)
    assert metrics["timeliness"] == "overdue"
    assert metrics["days_total"] == 1
    assert metrics["days_elapsed"] == 2
    assert metrics["days_remaining"] <= -1


@pytest.mark.asyncio
async def test_update_assignees_idempotent(session: AsyncSession) -> None:
    service = TaskService(user_client=DummyUserClient())
    project_repo = ProjectRepository()
    project = await project_repo.create(session, ProjectCreate(name="p", slug="p"))
    task_in = TaskCreate(project_id=project.id, title="t", assignee_ids=[1])
    task = await service.create(session, task_in)
    assert task.assignee_ids == [1]

    updated = await service.update(session, task.id, {"assignee_ids": [1]})
    assert updated and updated.assignee_ids == [1]
    updated = await service.update(session, task.id, {"assignee_ids": [1]})
    assert updated and updated.assignee_ids == [1]


@pytest.mark.asyncio
async def test_generate_code(session: AsyncSession) -> None:
    service = TaskService(user_client=DummyUserClient())
    project_repo = ProjectRepository()
    project = await project_repo.create(session, ProjectCreate(name="Proj", slug="abc"))

    t1 = await service.create(session, TaskCreate(project_id=project.id, title="a"))
    t2 = await service.create(session, TaskCreate(project_id=project.id, title="b"))
    assert t1.code == "ABC-1"
    assert t2.code == "ABC-2"
