"""List API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_session
from ..domain.schemas import ListCreate, ListRead
from ..services import ListService

router = APIRouter(tags=["lists"])


def get_list_service() -> ListService:
    return ListService()


class ListCreateBody(BaseModel):
    name: str
    position: int | None = None


class ListUpdate(BaseModel):
    name: str | None = None
    position: int | None = None


@router.post(
    "/projects/{project_id}/lists",
    response_model=ListRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_list(
    project_id: int,
    list_in: ListCreateBody,
    session: AsyncSession = Depends(get_session),
    service: ListService = Depends(get_list_service),
) -> ListRead:
    """Create a new list within a project."""
    list_data = list_in.model_dump()
    lst = await service.create(session, ListCreate(project_id=project_id, **list_data))
    return ListRead.model_validate(lst)


@router.get(
    "/projects/{project_id}/lists",
    response_model=dict[str, list[ListRead]],
)
async def list_lists(
    project_id: int,
    offset: int = 0,
    limit: int = Query(100, ge=1),
    session: AsyncSession = Depends(get_session),
    service: ListService = Depends(get_list_service),
) -> dict[str, list[ListRead]]:
    """List lists for a project."""
    lists = await service.list_by_project(
        session, project_id, offset=offset, limit=limit
    )
    data = [ListRead.model_validate(lst) for lst in lists]
    return {"lists": data}


@router.patch("/lists/{list_id}", response_model=ListRead)
async def update_list(
    list_id: int,
    list_in: ListUpdate,
    session: AsyncSession = Depends(get_session),
    service: ListService = Depends(get_list_service),
) -> ListRead:
    """Partially update a list."""
    data = list_in.model_dump(exclude_unset=True)
    lst = await service.update(session, list_id, data)
    if not lst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="List not found"
        )
    return ListRead.model_validate(lst)


__all__ = ["router"]
