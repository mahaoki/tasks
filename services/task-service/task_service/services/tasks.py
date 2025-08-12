from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from task_service.domain.models import Task
from task_service.domain.schemas import Status, TaskCreate, TaskRead
from task_service.repositories import ProjectRepository, TaskRepository
from task_service.services.user_client import UserServiceClient


class TaskService:
    """Business logic for :class:`~task_service.domain.models.Task`."""

    def __init__(
        self,
        repository: TaskRepository | None = None,
        project_repository: ProjectRepository | None = None,
        user_client: UserServiceClient | None = None,
    ) -> None:
        self.repository = repository or TaskRepository()
        self.project_repository = project_repository or ProjectRepository()
        self.user_client = user_client or UserServiceClient()

    async def create(self, session: AsyncSession, task_in: TaskCreate) -> TaskRead:
        await self._validate_assignees(task_in.assignee_ids)
        await self._validate_sector(task_in.sector_id)
        code = await self._generate_code(session, task_in.project_id)
        task_with_code = task_in.model_copy(update={"code": code})
        task = await self.repository.create(session, task_with_code)
        return self._to_read_model(task)

    async def get(self, session: AsyncSession, task_id: int) -> Optional[TaskRead]:
        task = await self.repository.get(session, task_id)
        if not task:
            return None
        return self._to_read_model(task)

    async def list(
        self,
        session: AsyncSession,
        *,
        project_id: Optional[int] = None,
        list_id: Optional[int] = None,
        status: Optional[str] = None,
        tag: Optional[str] = None,
        assignee_id: Optional[int] = None,
        sector_id: Optional[int] = None,
        complexity: Optional[str] = None,
        priority: Optional[str] = None,
        search: Optional[str] = None,
        timeliness: Optional[str] = None,
        order_by: Optional[str] = None,
        order: str = "asc",
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[TaskRead], int]:
        tasks = await self.repository.list(
            session,
            project_id=project_id,
            list_id=list_id,
            status=status,
            tag=tag,
            assignee_id=assignee_id,
            sector_id=sector_id,
            complexity=complexity,
            priority=priority,
            search=search,
            order_by=None if order_by == "timeliness" else order_by,
            order=order,
            offset=0,
            limit=None,
        )
        data = [self._to_read_model(task) for task in tasks]
        if timeliness is not None:
            data = [t for t in data if t.timeliness == timeliness]
        if order_by == "timeliness":
            order_map = {"on_time": 0, "late": 1, "overdue": 2, None: 3}
            data.sort(
                key=lambda t: order_map.get(t.timeliness, 3),
                reverse=order.lower() == "desc",
            )
        total = len(data)
        data = data[offset : offset + limit]
        return data, total

    async def move(
        self, session: AsyncSession, task_id: int, *, list_id: int
    ) -> Optional[TaskRead]:
        task = await self.repository.update(session, task_id, {"list_id": list_id})
        if not task:
            return None
        return self._to_read_model(task)

    async def archive(self, session: AsyncSession, task_id: int) -> Optional[TaskRead]:
        data = {"status": Status.COMPLETED.value, "completed_at": datetime.utcnow()}
        task = await self.repository.update(session, task_id, data)
        if not task:
            return None
        return self._to_read_model(task)

    async def update(
        self, session: AsyncSession, task_id: int, data: dict[str, Any]
    ) -> Optional[TaskRead]:
        if "assignee_ids" in data:
            await self._validate_assignees(data["assignee_ids"])
        if "sector_id" in data:
            await self._validate_sector(data["sector_id"])
        task = await self.repository.update(session, task_id, data)
        if not task:
            return None
        return self._to_read_model(task)

    async def delete(self, session: AsyncSession, task_id: int) -> bool:
        return await self.repository.delete(session, task_id)

    async def count_by_status(
        self, session: AsyncSession, *, project_id: Optional[int] = None
    ) -> dict[str, int]:
        return await self.repository.count_by_status(session, project_id=project_id)

    async def _generate_code(self, session: AsyncSession, project_id: int) -> str:
        project = await self.project_repository.get(session, project_id)
        if not project:
            raise ValueError("Project not found")
        seq = await self.repository.count_in_project(session, project_id) + 1
        return f"{project.slug.upper()}-{seq}"

    def _to_read_model(self, task: Task) -> TaskRead:
        data = TaskRead.model_validate(task)
        metrics = self._calculate_timeliness(task)
        return data.model_copy(update=metrics)

    def _calculate_timeliness(self, task: Task) -> dict[str, Any]:
        now = datetime.utcnow()
        start = task.start_date
        due = task.due_date
        completed = task.completed_at
        days_total = (due - start).days if start and due else None
        days_elapsed = ((completed or now) - start).days if start else None
        days_remaining = (due - (completed or now)).days if due else None
        timeliness: str | None = None
        if completed and due:
            timeliness = "on_time" if completed <= due else "late"
        elif not completed and due and now > due:
            timeliness = "overdue"
        return {
            "timeliness": timeliness,
            "days_total": days_total,
            "days_elapsed": days_elapsed,
            "days_remaining": days_remaining,
        }

    async def _validate_assignees(self, assignee_ids: List[int]) -> None:
        await self.user_client.verify_users(assignee_ids)

    async def _validate_sector(self, sector_id: int | None) -> None:
        if sector_id is None:
            return
        await self.user_client.get_sector_name(sector_id)
