from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.models import Comment
from ..domain.schemas import CommentCreate


class CommentRepository:
    async def create(self, session: AsyncSession, comment_in: CommentCreate) -> Comment:
        comment = Comment(**comment_in.model_dump())
        session.add(comment)
        await session.commit()
        await session.refresh(comment)
        return comment

    async def get(self, session: AsyncSession, comment_id: int) -> Optional[Comment]:
        return await session.get(Comment, comment_id)

    async def list_by_task(
        self,
        session: AsyncSession,
        task_id: int,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Comment]:
        stmt: Select[tuple[Comment]] = (
            select(Comment)
            .where(Comment.task_id == task_id)
            .order_by(Comment.created_at)
            .offset(offset)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    async def update(
        self, session: AsyncSession, comment_id: int, data: dict[str, Any]
    ) -> Optional[Comment]:
        comment = await self.get(session, comment_id)
        if not comment:
            return None
        for key, value in data.items():
            setattr(comment, key, value)
        await session.commit()
        await session.refresh(comment)
        return comment

    async def delete(self, session: AsyncSession, comment_id: int) -> bool:
        comment = await self.get(session, comment_id)
        if not comment:
            return False
        await session.delete(comment)
        await session.commit()
        return True

    async def count_by_task(self, session: AsyncSession, task_id: int) -> int:
        stmt = select(func.count(Comment.id)).where(Comment.task_id == task_id)
        result = await session.execute(stmt)
        return result.scalar_one()
