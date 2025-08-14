from __future__ import annotations

from enum import Enum
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


class ProjectRole(str, Enum):
    OWNER = "owner"
    MEMBER = "member"
    VIEWER = "viewer"


class ProjectMemberUpdate(BaseModel):
    role: ProjectRole


class ProjectMemberRead(ProjectMemberUpdate):
    user_id: UUID

    class Config:
        from_attributes = True
