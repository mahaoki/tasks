#!/usr/bin/env python
"""Seed initial data for the task service."""
from __future__ import annotations

import asyncio
from datetime import datetime
import sys
from pathlib import Path

import httpx

sys.path.append(
    str(Path(__file__).resolve().parents[1] / "services/task-service")
)

from task_service.core.database import async_session_factory
from task_service.core.settings import settings
from task_service.domain.schemas import (
    ListCreate,
    ProjectCreate,
    Status,
    TaskCreate,
)
from task_service.services import ListService, ProjectService, TaskService

DEFAULT_LISTS = ["Backlog", "In Progress", "Done"]
ADMIN_USER_ID = 1


async def seed() -> None:
    async with async_session_factory() as session:
        project_service = ProjectService()
        list_service = ListService()
        task_service = TaskService()

        # Create project
        project = await project_service.get_by_slug(session, "MKT")
        if project is None:
            project = await project_service.create(
                session, ProjectCreate(name="Marketing", slug="MKT")
            )

        # Create default lists
        existing_lists = await list_service.list_by_project(session, project.id)
        list_map = {lst.name: lst for lst in existing_lists}
        lists: list = []
        for position, name in enumerate(DEFAULT_LISTS, start=1):
            lst = list_map.get(name)
            if lst is None:
                lst = await list_service.create(
                    session,
                    ListCreate(project_id=project.id, name=name, position=position),
                )
            lists.append(lst)

        # Create demo tasks
        tasks_info = [
            {
                "title": "Market research",
                "list_id": lists[0].id,
                "status": Status.PENDING,
            },
            {
                "title": "Design campaign",
                "list_id": lists[1].id,
                "status": Status.IN_PROGRESS,
            },
            {
                "title": "Launch ads",
                "list_id": lists[2].id,
                "status": Status.COMPLETED,
                "completed_at": datetime.utcnow(),
            },
        ]
        for info in tasks_info:
            await task_service.create(
                session,
                TaskCreate(
                    project_id=project.id,
                    list_id=info["list_id"],
                    title=info["title"],
                    status=info["status"],
                    completed_at=info.get("completed_at"),
                ),
            )

    # Associate Admin user as project owner via user service
    async with httpx.AsyncClient(
        base_url=str(settings.user_service_base_url)
    ) as client:
        await client.put(
            f"/projects/{project.id}/members/{ADMIN_USER_ID}",
            json={"role": "owner"},
        )


if __name__ == "__main__":
    asyncio.run(seed())
