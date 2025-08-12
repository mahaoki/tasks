"""Health and metrics endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_session
from ..core.metrics import TASKS_STATUS_GAUGE
from ..services import TaskService

router = APIRouter()


def get_task_service() -> TaskService:
    return TaskService()


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/metrics")
async def metrics(
    session: AsyncSession = Depends(get_session),
    service: TaskService = Depends(get_task_service),
) -> Response:
    counts = await service.count_by_status(session)
    for status, count in counts.items():
        TASKS_STATUS_GAUGE.labels(status=status).set(count)
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


__all__ = ["router"]
