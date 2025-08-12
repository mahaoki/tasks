from __future__ import annotations

from typing import Optional

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.models import ActivityLog
from ..domain.schemas import ActivityLogCreate


class ActivityLogRepository:
    async def create(
        self, session: AsyncSession, activity_in: ActivityLogCreate
    ) -> ActivityLog:
        activity = ActivityLog(**activity_in.model_dump())
        session.add(activity)
        await session.commit()
        await session.refresh(activity)
        return activity

    async def get(
        self, session: AsyncSession, activity_id: int
    ) -> Optional[ActivityLog]:
        return await session.get(ActivityLog, activity_id)

    async def list(
        self,
        session: AsyncSession,
        *,
        task_id: Optional[int] = None,
        performed_by: Optional[int] = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[ActivityLog]:
        stmt: Select[tuple[ActivityLog]] = select(ActivityLog)
        if task_id is not None:
            stmt = stmt.where(ActivityLog.task_id == task_id)
        if performed_by is not None:
            stmt = stmt.where(ActivityLog.performed_by == performed_by)
        stmt = stmt.order_by(ActivityLog.created_at.desc()).offset(offset).limit(limit)
        result = await session.execute(stmt)
        return result.scalars().all()

    async def delete(self, session: AsyncSession, activity_id: int) -> bool:
        activity = await self.get(session, activity_id)
        if not activity:
            return False
        await session.delete(activity)
        await session.commit()
        return True

    async def count_by_action(
        self, session: AsyncSession, *, task_id: Optional[int] = None
    ) -> dict[str, int]:
        stmt = select(ActivityLog.action, func.count(ActivityLog.id)).group_by(
            ActivityLog.action
        )
        if task_id is not None:
            stmt = stmt.where(ActivityLog.task_id == task_id)
        result = await session.execute(stmt)
        return {action: count for action, count in result.all()}
