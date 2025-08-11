from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from task_service.domain.models import Task
from task_service.domain.schemas import TaskCreate


class TaskRepository:
    async def create(self, session: AsyncSession, task_in: TaskCreate) -> Task:
        task = Task(**task_in.model_dump())
        session.add(task)
        await session.commit()
        await session.refresh(task)
        return task

    async def get(self, session: AsyncSession, task_id: int) -> Optional[Task]:
        return await session.get(Task, task_id)

    async def list(
        self,
        session: AsyncSession,
        *,
        project_id: Optional[int] = None,
        list_id: Optional[int] = None,
        status: Optional[str] = None,
        tag: Optional[str] = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Task]:
        stmt: Select[tuple[Task]] = select(Task)
        if project_id is not None:
            stmt = stmt.where(Task.project_id == project_id)
        if list_id is not None:
            stmt = stmt.where(Task.list_id == list_id)
        if status is not None:
            stmt = stmt.where(Task.status == status)
        if tag is not None:
            stmt = stmt.where(Task.tags.contains([tag]))
        stmt = stmt.offset(offset).limit(limit)
        result = await session.execute(stmt)
        return result.scalars().all()

    async def update(
        self, session: AsyncSession, task_id: int, data: dict[str, Any]
    ) -> Optional[Task]:
        task = await self.get(session, task_id)
        if not task:
            return None
        for key, value in data.items():
            setattr(task, key, value)
        await session.commit()
        await session.refresh(task)
        return task

    async def delete(self, session: AsyncSession, task_id: int) -> bool:
        task = await self.get(session, task_id)
        if not task:
            return False
        await session.delete(task)
        await session.commit()
        return True

    async def count_by_status(
        self, session: AsyncSession, *, project_id: Optional[int] = None
    ) -> dict[str, int]:
        stmt = select(Task.status, func.count(Task.id)).group_by(Task.status)
        if project_id is not None:
            stmt = stmt.where(Task.project_id == project_id)
        result = await session.execute(stmt)
        return {status: count for status, count in result.all()}

    async def count_in_project(self, session: AsyncSession, project_id: int) -> int:
        stmt = select(func.count(Task.id)).where(Task.project_id == project_id)
        result = await session.execute(stmt)
        return result.scalar_one()
