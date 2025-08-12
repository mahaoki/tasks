from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.models import List
from ..domain.schemas import ListCreate
from ..repositories import ListRepository


class ListService:
    """Business logic for :class:`~app.domain.models.List`."""

    def __init__(self, repository: ListRepository | None = None) -> None:
        self.repository = repository or ListRepository()

    async def create(self, session: AsyncSession, list_in: ListCreate) -> List:
        return await self.repository.create(session, list_in)

    async def get(self, session: AsyncSession, list_id: int) -> Optional[List]:
        return await self.repository.get(session, list_id)

    async def list_by_project(
        self,
        session: AsyncSession,
        project_id: int,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[List]:
        return await self.repository.list_by_project(
            session, project_id, offset=offset, limit=limit
        )

    async def update(
        self, session: AsyncSession, list_id: int, data: dict[str, Any]
    ) -> Optional[List]:
        return await self.repository.update(session, list_id, data)

    async def delete(self, session: AsyncSession, list_id: int) -> bool:
        return await self.repository.delete(session, list_id)

    async def task_count(self, session: AsyncSession, list_id: int) -> int:
        return await self.repository.task_count(session, list_id)
