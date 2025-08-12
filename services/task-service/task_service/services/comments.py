from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from task_service.domain.models import Comment
from task_service.domain.schemas import CommentCreate
from task_service.repositories import CommentRepository


class CommentService:
    """Business logic for :class:`~task_service.domain.models.Comment`."""

    def __init__(self, repository: CommentRepository | None = None) -> None:
        self.repository = repository or CommentRepository()

    async def create(self, session: AsyncSession, comment_in: CommentCreate) -> Comment:
        return await self.repository.create(session, comment_in)

    async def get(self, session: AsyncSession, comment_id: int) -> Optional[Comment]:
        return await self.repository.get(session, comment_id)

    async def list_by_task(
        self, session: AsyncSession, task_id: int, *, offset: int = 0, limit: int = 100
    ) -> list[Comment]:
        return await self.repository.list_by_task(
            session, task_id, offset=offset, limit=limit
        )

    async def update(
        self, session: AsyncSession, comment_id: int, data: dict[str, Any]
    ) -> Optional[Comment]:
        return await self.repository.update(session, comment_id, data)

    async def delete(self, session: AsyncSession, comment_id: int) -> bool:
        return await self.repository.delete(session, comment_id)

    async def count_by_task(self, session: AsyncSession, task_id: int) -> int:
        return await self.repository.count_by_task(session, task_id)
