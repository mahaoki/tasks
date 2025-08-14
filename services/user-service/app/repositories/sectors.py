from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from .. import models


class SectorRepository:
    """Data access layer for sectors."""

    async def get(
        self, session: AsyncSession, sector_id: UUID
    ) -> models.Sector | None:
        return await session.get(models.Sector, sector_id)
