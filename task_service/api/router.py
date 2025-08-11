from fastapi import APIRouter

from .lists import router as lists_router
from .projects import router as projects_router

router = APIRouter()
router.include_router(projects_router)
router.include_router(lists_router)


@router.get("/", summary="List tasks")
async def list_tasks() -> dict[str, list]:
    """Return an empty list of tasks."""
    return {"tasks": []}
