"""Comment API endpoints."""

from __future__ import annotations

import re

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_session
from ..domain.schemas import CommentCreate, CommentRead
from ..services import CommentService

router = APIRouter(tags=["comments"])


def get_comment_service() -> CommentService:
    return CommentService()


class CommentCreateBody(BaseModel):
    content: str
    author_id: int | None = None


def parse_mentions(text: str) -> list[str]:
    """Extract ``@user`` mentions from ``text``."""

    return re.findall(r"@([A-Za-z0-9_]+)", text)


@router.post(
    "/tasks/{task_id}/comments",
    response_model=CommentRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    task_id: int,
    comment_in: CommentCreateBody,
    session: AsyncSession = Depends(get_session),
    service: CommentService = Depends(get_comment_service),
) -> CommentRead:
    data = comment_in.model_dump()
    comment = await service.create(session, CommentCreate(task_id=task_id, **data))
    base = CommentRead.model_validate(comment)
    return base.model_copy(update={"mentions": parse_mentions(base.content)})


@router.get(
    "/tasks/{task_id}/comments",
    response_model=dict[str, list[CommentRead]],
)
async def list_comments(
    task_id: int,
    offset: int = 0,
    limit: int = Query(100, ge=1),
    session: AsyncSession = Depends(get_session),
    service: CommentService = Depends(get_comment_service),
) -> dict[str, list[CommentRead]]:
    comments = await service.list_by_task(session, task_id, offset=offset, limit=limit)
    data: list[CommentRead] = []
    for comment in comments:
        base = CommentRead.model_validate(comment)
        data.append(base.model_copy(update={"mentions": parse_mentions(base.content)}))
    return {"comments": data}


__all__ = ["router"]
