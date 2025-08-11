from __future__ import annotations

from sqlalchemy.orm import Session

from . import models


def seed_initial_data(db: Session) -> None:
    # Seed roles
    if not db.query(models.Role).first():
        db.add_all(
            [
                models.Role(name="admin"),
                models.Role(name="manager"),
                models.Role(name="user"),
            ]
        )
        db.commit()
    # Seed sectors
    if not db.query(models.Sector).first():
        gerente = models.Sector(name="Gerente")
        db.add(gerente)
        db.commit()
    # Seed admin user
    admin = db.query(models.User).filter_by(email="admin@example.com").first()
    if not admin:
        admin = models.User(email="admin@example.com", full_name="Admin")
        admin_role = db.query(models.Role).filter_by(name="admin").first()
        gerente_sector = db.query(models.Sector).filter_by(name="Gerente").first()
        if admin_role:
            admin.roles.append(admin_role)
        if gerente_sector:
            admin.sectors.append(gerente_sector)
        db.add(admin)
        db.commit()
