from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, EmailStr


class RoleRead(BaseModel):
    id: UUID
    name: str

    class Config:
        from_attributes = True


class SectorRead(BaseModel):
    id: UUID
    name: str

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str | None = None
    roles: list[str] = []  # role names
    sectors: list[str] = []  # sector names


class UserUpdate(BaseModel):
    full_name: str | None = None
    roles: list[str] | None = None
    sectors: list[str] | None = None


class UserRead(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str | None = None
    roles: list[RoleRead] = []
    sectors: list[SectorRead] = []

    class Config:
        from_attributes = True
