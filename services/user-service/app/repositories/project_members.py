from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models


class ProjectMemberRepository:
    """Data access layer for project members."""

    async def list(
        self, session: AsyncSession, project_id: int
    ) -> list[models.ProjectMember]:
        stmt = select(models.ProjectMember).where(
            models.ProjectMember.project_id == project_id
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    async def upsert(
        self,
        session: AsyncSession,
        project_id: int,
        user_id: UUID,
        role: str,
    ) -> models.ProjectMember:
        member = await session.get(
            models.ProjectMember, {"project_id": project_id, "user_id": user_id}
        )
        if member:
            member.role = role
        else:
            member = models.ProjectMember(
                project_id=project_id, user_id=user_id, role=role
            )
            session.add(member)
        await session.commit()
        await session.refresh(member)
        return member

    async def delete(
        self, session: AsyncSession, project_id: int, user_id: UUID
    ) -> bool:
        member = await session.get(
            models.ProjectMember, {"project_id": project_id, "user_id": user_id}
        )
        if not member:
            return False
        await session.delete(member)
        await session.commit()
        return True
