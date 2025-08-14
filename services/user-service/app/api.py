from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from . import models, schemas, security
from .database import get_db
from .repositories import ProjectMemberRepository

router = APIRouter()


@router.get("/users/me", response_model=schemas.UserRead)
async def read_me(
    payload: dict = Depends(security.get_current_payload),
    db: AsyncSession = Depends(get_db),
):
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid token")
    user = await db.get(
        models.User,
        UUID(str(user_id)),
        options=[
            selectinload(models.User.roles),
            selectinload(models.User.sectors),
        ],
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/users", response_model=list[schemas.UserRead])
async def list_users(
    page: int = 1,
    page_size: int = 10,
    ids: str | None = None,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(security.require_roles(["admin", "manager"])),
):
    stmt = select(models.User).options(
        selectinload(models.User.roles),
        selectinload(models.User.sectors),
    )

    if ids:
        try:
            id_list = [UUID(id_str) for id_str in ids.split(",")]
        except ValueError as exc:  # pragma: no cover - simple validation
            raise HTTPException(status_code=400, detail="Invalid ids") from exc
        stmt = stmt.where(models.User.id.in_(id_list))
    else:
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

    result = await db.execute(stmt)
    users = result.scalars().all()
    return users


@router.post("/users", response_model=schemas.UserRead, status_code=201)
async def create_user(
    user_in: schemas.UserCreate,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(security.require_roles(["admin", "manager"], ["user"])),
):
    security.enforce_allowed_roles(payload, user_in.roles)
    existing = (
        (await db.execute(select(models.User).filter_by(email=user_in.email)))
        .scalars()
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = models.User(email=user_in.email, full_name=user_in.full_name)
    if user_in.roles:
        roles_result = await db.execute(
            select(models.Role).filter(models.Role.name.in_(user_in.roles))
        )
        user.roles = roles_result.scalars().all()
    if user_in.sectors:
        sectors_result = await db.execute(
            select(models.Sector).filter(models.Sector.name.in_(user_in.sectors))
        )
        user.sectors = sectors_result.scalars().all()
    db.add(user)
    await db.commit()
    await db.refresh(user, attribute_names=["roles", "sectors"])
    return user


@router.patch("/users/{user_id}", response_model=schemas.UserRead)
async def update_user(
    user_id: UUID,
    user_in: schemas.UserUpdate,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(security.require_roles(["admin", "manager"], ["user"])),
):
    user = await db.get(
        models.User,
        user_id,
        options=[
            selectinload(models.User.roles),
            selectinload(models.User.sectors),
        ],
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if "manager" in payload.get("roles", []) and any(
        r.name != "user" for r in user.roles
    ):
        raise HTTPException(
            status_code=403, detail="Managers can only manage collaborators"
        )
    security.enforce_allowed_roles(payload, user_in.roles or [])
    if user_in.full_name is not None:
        user.full_name = user_in.full_name
    if user_in.roles is not None:
        roles_result = await db.execute(
            select(models.Role).filter(models.Role.name.in_(user_in.roles))
        )
        user.roles = roles_result.scalars().all()
    if user_in.sectors is not None:
        sectors_result = await db.execute(
            select(models.Sector).filter(models.Sector.name.in_(user_in.sectors))
        )
        user.sectors = sectors_result.scalars().all()
    await db.commit()
    await db.refresh(user, attribute_names=["roles", "sectors"])
    return user


@router.get("/roles", response_model=list[schemas.RoleRead])
async def list_roles(
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(security.require_roles(["admin", "manager"])),
):
    result = await db.execute(select(models.Role))
    return result.scalars().all()


@router.get("/sectors", response_model=list[schemas.SectorRead])
async def list_sectors(
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(security.get_current_payload),
):
    result = await db.execute(select(models.Sector))
    return result.scalars().all()


project_member_repo = ProjectMemberRepository()


@router.get(
    "/projects/{project_id}/members",
    response_model=dict[str, list[schemas.ProjectMemberRead]],
)
async def list_project_members(
    project_id: int, db: AsyncSession = Depends(get_db)
) -> dict[str, list[schemas.ProjectMemberRead]]:
    members = await project_member_repo.list(db, project_id)
    return {"members": members}


@router.put(
    "/projects/{project_id}/members/{user_id}",
    response_model=schemas.ProjectMemberRead,
)
async def put_project_member(
    project_id: int,
    user_id: UUID,
    member_in: schemas.ProjectMemberUpdate,
    db: AsyncSession = Depends(get_db),
) -> schemas.ProjectMemberRead:
    user = await db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    member = await project_member_repo.upsert(
        db, project_id, user_id, member_in.role.value
    )
    return member


@router.delete("/projects/{project_id}/members/{user_id}", status_code=204)
async def delete_project_member(
    project_id: int, user_id: UUID, db: AsyncSession = Depends(get_db)
) -> Response:
    success = await project_member_repo.delete(db, project_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Member not found")
    return Response(status_code=204)
