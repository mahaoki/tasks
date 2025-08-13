from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from . import models


async def seed_initial_data(db: AsyncSession) -> None:
    # Seed roles
    roles_exist = (await db.execute(select(models.Role))).scalars().first()
    if not roles_exist:
        db.add_all(
            [
                models.Role(name="admin"),
                models.Role(name="manager"),
                models.Role(name="user"),
            ]
        )
        await db.commit()
    # Seed sectors
    sectors_exist = (await db.execute(select(models.Sector))).scalars().first()
    if not sectors_exist:
        gerente = models.Sector(name="Gerente")
        db.add(gerente)
        await db.commit()
    # Seed admin user
    admin = (
        (await db.execute(select(models.User).filter_by(email="admin@example.com")))
        .scalars()
        .first()
    )
    if not admin:
        admin = models.User(email="admin@example.com", full_name="Admin")
        admin_role = (
            (await db.execute(select(models.Role).filter_by(name="admin")))
            .scalars()
            .first()
        )
        gerente_sector = (
            (await db.execute(select(models.Sector).filter_by(name="Gerente")))
            .scalars()
            .first()
        )
        if admin_role:
            admin.roles.append(admin_role)
        if gerente_sector:
            admin.sectors.append(gerente_sector)
        db.add(admin)
        await db.commit()
