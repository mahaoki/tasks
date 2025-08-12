from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.models import Project, Task
from ..domain.schemas import ProjectCreate


class ProjectRepository:
    """Data access layer for :class:`~app.domain.models.Project`."""

    async def create(self, session: AsyncSession, project_in: ProjectCreate) -> Project:
        project = Project(**project_in.model_dump())
        session.add(project)
        await session.commit()
        await session.refresh(project)
        return project

    async def get(self, session: AsyncSession, project_id: int) -> Optional[Project]:
        return await session.get(Project, project_id)

    async def get_by_slug(self, session: AsyncSession, slug: str) -> Optional[Project]:
        stmt: Select[tuple[Project]] = select(Project).where(Project.slug == slug)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self, session: AsyncSession, *, offset: int = 0, limit: int = 100
    ) -> list[Project]:
        stmt: Select[tuple[Project]] = select(Project).offset(offset).limit(limit)
        result = await session.execute(stmt)
        return result.scalars().all()

    async def update(
        self,
        session: AsyncSession,
        project_id: int,
        data: dict[str, Any],
    ) -> Optional[Project]:
        project = await self.get(session, project_id)
        if not project:
            return None
        for key, value in data.items():
            setattr(project, key, value)
        await session.commit()
        await session.refresh(project)
        return project

    async def delete(self, session: AsyncSession, project_id: int) -> bool:
        project = await self.get(session, project_id)
        if not project:
            return False
        await session.delete(project)
        await session.commit()
        return True

    async def task_statistics(
        self, session: AsyncSession, project_id: int
    ) -> dict[str, int]:
        stmt = (
            select(Task.status, func.count(Task.id))
            .where(Task.project_id == project_id)
            .group_by(Task.status)
        )
        result = await session.execute(stmt)
        return {status: count for status, count in result.all()}
