"""Task API endpoints."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from task_service.core.database import get_session
from task_service.domain.schemas import (Complexity, Priority, Status,
                                         TaskCreate, TaskRead)
from task_service.services import TaskService

router = APIRouter(tags=["tasks"])


def get_task_service() -> TaskService:
    return TaskService()


class TaskCreateBody(BaseModel):
    list_id: int | None = None
    title: str
    description: str | None = None
    status: Status = Status.PENDING
    complexity: Complexity | None = None
    priority: Priority | None = None
    start_date: datetime | None = None
    due_date: datetime | None = None
    completed_at: datetime | None = None
    assignee_ids: list[int] = []
    sector_id: int | None = None
    tags: list[str] = []


class TaskUpdate(BaseModel):
    list_id: int | None = None
    title: str | None = None
    description: str | None = None
    status: Status | None = None
    complexity: Complexity | None = None
    priority: Priority | None = None
    start_date: datetime | None = None
    due_date: datetime | None = None
    completed_at: datetime | None = None
    assignee_ids: list[int] | None = None
    sector_id: int | None = None
    tags: list[str] | None = None


class MoveTaskBody(BaseModel):
    list_id: int


@router.post(
    "/projects/{project_id}/tasks",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    project_id: int,
    task_in: TaskCreateBody,
    session: AsyncSession = Depends(get_session),
    service: TaskService = Depends(get_task_service),
) -> TaskRead:
    data = task_in.model_dump()
    task = await service.create(session, TaskCreate(project_id=project_id, **data))
    return task


@router.get(
    "/projects/{project_id}/tasks",
    response_model=dict[str, list[TaskRead]],
)
async def list_tasks(
    project_id: int,
    list_id: int | None = None,
    status: Status | None = None,
    tag: str | None = None,
    assignee_id: int | None = None,
    sector_id: int | None = None,
    complexity: Complexity | None = None,
    priority: Priority | None = None,
    search: str | None = None,
    timeliness: str | None = None,
    order_by: str | None = None,
    order: str = "asc",
    offset: int = 0,
    limit: int = Query(100, ge=1),
    session: AsyncSession = Depends(get_session),
    service: TaskService = Depends(get_task_service),
) -> dict[str, list[TaskRead]]:
    tasks = await service.list(
        session,
        project_id=project_id,
        list_id=list_id,
        status=status,
        tag=tag,
        assignee_id=assignee_id,
        sector_id=sector_id,
        complexity=complexity,
        priority=priority,
        search=search,
        timeliness=timeliness,
        order_by=order_by,
        order=order,
        offset=offset,
        limit=limit,
    )
    return {"tasks": tasks}


@router.get("/tasks/{task_id}", response_model=TaskRead)
async def get_task(
    task_id: int,
    session: AsyncSession = Depends(get_session),
    service: TaskService = Depends(get_task_service),
) -> TaskRead:
    task = await service.get(session, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    return task


@router.patch("/tasks/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: int,
    task_in: TaskUpdate,
    session: AsyncSession = Depends(get_session),
    service: TaskService = Depends(get_task_service),
) -> TaskRead:
    data = task_in.model_dump(exclude_unset=True)
    task = await service.update(session, task_id, data)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    return task


@router.post("/tasks/{task_id}/move", response_model=TaskRead)
async def move_task(
    task_id: int,
    body: MoveTaskBody,
    session: AsyncSession = Depends(get_session),
    service: TaskService = Depends(get_task_service),
) -> TaskRead:
    task = await service.move(session, task_id, list_id=body.list_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    return task


@router.post("/tasks/{task_id}/archive", response_model=TaskRead)
async def archive_task(
    task_id: int,
    session: AsyncSession = Depends(get_session),
    service: TaskService = Depends(get_task_service),
) -> TaskRead:
    task = await service.archive(session, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    return task


__all__ = ["router"]
