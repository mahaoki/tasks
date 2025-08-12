"""Project API endpoints."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_session
from ..core.settings import settings
from ..domain.schemas import (
    ProjectCreate,
    ProjectMemberRead,
    ProjectMemberUpdate,
    ProjectRead,
)
from ..services import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


def get_project_service() -> ProjectService:
    return ProjectService()


class ProjectUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None


@router.post("/", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_in: ProjectCreate,
    session: AsyncSession = Depends(get_session),
    service: ProjectService = Depends(get_project_service),
) -> ProjectRead:
    """Create a new project."""
    project = await service.create(session, project_in)
    return ProjectRead.model_validate(project)


@router.get("/", response_model=dict[str, list[ProjectRead]])
async def list_projects(
    offset: int = 0,
    limit: int = Query(100, ge=1),
    session: AsyncSession = Depends(get_session),
    service: ProjectService = Depends(get_project_service),
) -> dict[str, list[ProjectRead]]:
    """List projects."""
    projects = await service.list(session, offset=offset, limit=limit)
    data = [ProjectRead.model_validate(p) for p in projects]
    return {"projects": data}


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: int,
    session: AsyncSession = Depends(get_session),
    service: ProjectService = Depends(get_project_service),
) -> ProjectRead:
    """Retrieve a project by its ID."""
    project = await service.get(session, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    return ProjectRead.model_validate(project)


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: int,
    project_in: ProjectUpdate,
    session: AsyncSession = Depends(get_session),
    service: ProjectService = Depends(get_project_service),
) -> ProjectRead:
    """Partially update a project."""
    data = project_in.model_dump(exclude_unset=True)
    project = await service.update(session, project_id, data)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    return ProjectRead.model_validate(project)


@router.get("/{project_id}/members", response_model=dict[str, list[ProjectMemberRead]])
async def list_members(project_id: int) -> dict[str, list[ProjectMemberRead]]:
    """List members of a project.

    This endpoint proxies the request to the user service.
    """
    async with httpx.AsyncClient(
        base_url=str(settings.user_service_base_url)
    ) as client:
        resp = await client.get(f"/projects/{project_id}/members")
    if resp.status_code == status.HTTP_404_NOT_FOUND:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    resp.raise_for_status()
    data = resp.json()
    members = data.get("members", data)
    return {"members": [ProjectMemberRead.model_validate(m) for m in members]}


@router.put(
    "/{project_id}/members/{user_id}",
    response_model=ProjectMemberRead,
    status_code=status.HTTP_200_OK,
)
async def put_member(
    project_id: int,
    user_id: int,
    member_in: ProjectMemberUpdate,
) -> ProjectMemberRead:
    """Add or update a project member by delegating to the user service."""
    async with httpx.AsyncClient(
        base_url=str(settings.user_service_base_url)
    ) as client:
        resp = await client.put(
            f"/projects/{project_id}/members/{user_id}",
            json=member_in.model_dump(),
        )
    if resp.status_code == status.HTTP_404_NOT_FOUND:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Member not found"
        )
    resp.raise_for_status()
    return ProjectMemberRead.model_validate(resp.json())


@router.delete(
    "/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_member(project_id: int, user_id: int) -> Response:
    """Remove a project member via the user service."""
    async with httpx.AsyncClient(
        base_url=str(settings.user_service_base_url)
    ) as client:
        resp = await client.delete(f"/projects/{project_id}/members/{user_id}")
    if resp.status_code == status.HTTP_404_NOT_FOUND:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Member not found"
        )
    resp.raise_for_status()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


__all__ = ["router"]
