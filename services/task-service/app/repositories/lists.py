from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.models import List, Task
from ..domain.schemas import ListCreate


class ListRepository:
    async def create(self, session: AsyncSession, list_in: ListCreate) -> List:
        lst = List(**list_in.model_dump())
        session.add(lst)
        await session.commit()
        await session.refresh(lst)
        return lst

    async def get(self, session: AsyncSession, list_id: int) -> Optional[List]:
        return await session.get(List, list_id)

    async def list_by_project(
        self,
        session: AsyncSession,
        project_id: int,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[List]:
        stmt: Select[tuple[List]] = (
            select(List)
            .where(List.project_id == project_id)
            .order_by(List.position)
            .offset(offset)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    async def update(
        self, session: AsyncSession, list_id: int, data: dict[str, Any]
    ) -> Optional[List]:
        lst = await self.get(session, list_id)
        if not lst:
            return None
        for key, value in data.items():
            setattr(lst, key, value)
        await session.commit()
        await session.refresh(lst)
        return lst

    async def delete(self, session: AsyncSession, list_id: int) -> bool:
        lst = await self.get(session, list_id)
        if not lst:
            return False
        await session.delete(lst)
        await session.commit()
        return True

    async def task_count(self, session: AsyncSession, list_id: int) -> int:
        stmt = select(func.count(Task.id)).where(Task.list_id == list_id)
        result = await session.execute(stmt)
        return result.scalar_one()
