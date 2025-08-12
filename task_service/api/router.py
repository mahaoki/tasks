from fastapi import APIRouter

from .lists import router as lists_router
from .projects import router as projects_router
from .tasks import router as tasks_router

router = APIRouter()
router.include_router(projects_router)
router.include_router(lists_router)
router.include_router(tasks_router)
