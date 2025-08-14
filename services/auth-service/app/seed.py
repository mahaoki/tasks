from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from . import models, security


async def seed_initial_data(db: AsyncSession) -> None:
    admin = (
        (await db.execute(select(models.AuthUser).filter_by(email="admin@example.com")))
        .scalars()
        .first()
    )
    if not admin:
        admin = models.AuthUser(
            email="admin@example.com",
            password_hash=security.hash_password("admin"),
        )
        db.add(admin)
        await db.commit()
