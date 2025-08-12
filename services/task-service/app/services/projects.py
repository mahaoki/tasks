from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.models import Project
from ..domain.schemas import ProjectCreate
from ..repositories import ProjectRepository


class ProjectService:
    """Business logic for :class:`~app.domain.models.Project`."""

    def __init__(self, repository: ProjectRepository | None = None) -> None:
        self.repository = repository or ProjectRepository()

    async def create(self, session: AsyncSession, project_in: ProjectCreate) -> Project:
        return await self.repository.create(session, project_in)

    async def get(self, session: AsyncSession, project_id: int) -> Optional[Project]:
        return await self.repository.get(session, project_id)

    async def get_by_slug(self, session: AsyncSession, slug: str) -> Optional[Project]:
        return await self.repository.get_by_slug(session, slug)

    async def list(
        self, session: AsyncSession, *, offset: int = 0, limit: int = 100
    ) -> list[Project]:
        return await self.repository.list(session, offset=offset, limit=limit)

    async def update(
        self, session: AsyncSession, project_id: int, data: dict[str, Any]
    ) -> Optional[Project]:
        return await self.repository.update(session, project_id, data)

    async def delete(self, session: AsyncSession, project_id: int) -> bool:
        return await self.repository.delete(session, project_id)

    async def task_statistics(
        self, session: AsyncSession, project_id: int
    ) -> dict[str, int]:
        return await self.repository.task_statistics(session, project_id)
