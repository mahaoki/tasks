from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from .models import AuditLog


def log_event(
    db: Session,
    action: str,
    user_id: Optional[UUID] = None,
    ip: str | None = None,
    user_agent: str | None = None,
) -> None:
    entry = AuditLog(user_id=user_id, action=action, ip_address=ip, user_agent=user_agent)
    db.add(entry)
    db.commit()
