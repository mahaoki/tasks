from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from .models import AuditLog


async def log_event(
    db: AsyncSession,
    action: str,
    user_id: Optional[UUID] = None,
    ip: str | None = None,
    user_agent: str | None = None,
) -> None:
    entry = AuditLog(user_id=user_id, action=action, ip_address=ip, user_agent=user_agent)
    db.add(entry)
    await db.commit()
