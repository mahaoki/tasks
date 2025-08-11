from fastapi import APIRouter

router = APIRouter()


@router.get("/", summary="List tasks")
async def list_tasks() -> dict[str, list]:
    """Return an empty list of tasks."""
    return {"tasks": []}
