from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from . import models, schemas, security
from .database import get_db

router = APIRouter()


@router.get("/users/me", response_model=schemas.UserRead)
def read_me(
    payload: dict = Depends(security.get_current_payload),
    db: Session = Depends(get_db),
):
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid token")
    user = db.get(models.User, UUID(str(user_id)))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/users", response_model=list[schemas.UserRead])
def list_users(
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db),
    payload: dict = Depends(security.require_roles(["admin"])),
):
    offset = (page - 1) * page_size
    users = db.query(models.User).offset(offset).limit(page_size).all()
    return users


@router.post("/users", response_model=schemas.UserRead, status_code=201)
def create_user(
    user_in: schemas.UserCreate,
    db: Session = Depends(get_db),
    payload: dict = Depends(security.require_roles(["admin"])),
):
    existing = db.query(models.User).filter_by(email=user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = models.User(email=user_in.email, full_name=user_in.full_name)
    if user_in.roles:
        roles = db.query(models.Role).filter(models.Role.name.in_(user_in.roles)).all()
        user.roles = roles
    if user_in.sectors:
        sectors = (
            db.query(models.Sector)
            .filter(models.Sector.name.in_(user_in.sectors))
            .all()
        )
        user.sectors = sectors
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}", response_model=schemas.UserRead)
def update_user(
    user_id: UUID,
    user_in: schemas.UserUpdate,
    db: Session = Depends(get_db),
    payload: dict = Depends(security.require_roles(["admin"])),
):
    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user_in.full_name is not None:
        user.full_name = user_in.full_name
    if user_in.roles is not None:
        roles = db.query(models.Role).filter(models.Role.name.in_(user_in.roles)).all()
        user.roles = roles
    if user_in.sectors is not None:
        sectors = (
            db.query(models.Sector)
            .filter(models.Sector.name.in_(user_in.sectors))
            .all()
        )
        user.sectors = sectors
    db.commit()
    db.refresh(user)
    return user


@router.get("/roles", response_model=list[schemas.RoleRead])
def list_roles(
    db: Session = Depends(get_db),
    payload: dict = Depends(security.require_roles(["admin"])),
):
    return db.query(models.Role).all()


@router.get("/sectors", response_model=list[schemas.SectorRead])
def list_sectors(
    db: Session = Depends(get_db),
    payload: dict = Depends(security.get_current_payload),
):
    return db.query(models.Sector).all()
