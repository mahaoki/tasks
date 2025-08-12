from __future__ import annotations

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from task_service.core import permissions, security


@pytest.fixture()
def app(monkeypatch) -> FastAPI:
    async def mock_user() -> dict[str, int | dict]:  # type: ignore[override]
        return {"user_id": "1", "sector_id": 5, "claims": {}}

    monkeypatch.setattr(security, "get_current_user", mock_user)
    monkeypatch.setattr(permissions, "get_current_user", mock_user)

    app = FastAPI()

    @app.post(
        "/projects/{project_id}/tasks",
        dependencies=[Depends(permissions.require_project_permission("create"))],
    )
    async def create_task(
        project_id: int,
    ) -> dict[str, str]:  # pragma: no cover - trivial
        return {"status": "created"}

    @app.patch(
        "/projects/{project_id}/tasks/{task_id}",
        dependencies=[Depends(permissions.require_project_permission("edit"))],
    )
    async def edit_task(
        project_id: int, task_id: int
    ) -> dict[str, str]:  # pragma: no cover - trivial
        return {"status": "edited"}

    @app.get(
        "/projects/{project_id}/tasks",
        dependencies=[Depends(permissions.require_project_permission("list"))],
    )
    async def list_tasks(
        project_id: int,
    ) -> dict[str, str]:  # pragma: no cover - trivial
        return {"status": "ok"}

    return app


def test_viewer_can_list(app: FastAPI, monkeypatch) -> None:
    async def mock_fetch(
        project_id: int, user_id: str, base_url: str | None = None
    ) -> str | None:
        return "Viewer"

    monkeypatch.setattr(permissions, "_fetch_project_role", mock_fetch)
    client = TestClient(app)
    resp = client.get("/projects/1/tasks")
    assert resp.status_code == 200


def test_contributor_can_create(app: FastAPI, monkeypatch) -> None:
    async def mock_fetch(
        project_id: int, user_id: str, base_url: str | None = None
    ) -> str | None:
        return "Contributor"

    monkeypatch.setattr(permissions, "_fetch_project_role", mock_fetch)
    client = TestClient(app)
    resp = client.post("/projects/1/tasks")
    assert resp.status_code == 200


def test_viewer_cannot_create(app: FastAPI, monkeypatch) -> None:
    async def mock_fetch(
        project_id: int, user_id: str, base_url: str | None = None
    ) -> str | None:
        return "Viewer"

    monkeypatch.setattr(permissions, "_fetch_project_role", mock_fetch)
    client = TestClient(app)
    resp = client.post("/projects/1/tasks")
    assert resp.status_code == 403


def test_viewer_cannot_edit(app: FastAPI, monkeypatch) -> None:
    async def mock_fetch(
        project_id: int, user_id: str, base_url: str | None = None
    ) -> str | None:
        return "Viewer"

    monkeypatch.setattr(permissions, "_fetch_project_role", mock_fetch)
    client = TestClient(app)
    resp = client.patch("/projects/1/tasks/1")
    assert resp.status_code == 403


def test_non_member_forbidden(app: FastAPI, monkeypatch) -> None:
    async def mock_fetch(
        project_id: int, user_id: str, base_url: str | None = None
    ) -> str | None:
        return None

    monkeypatch.setattr(permissions, "_fetch_project_role", mock_fetch)
    client = TestClient(app)
    resp = client.get("/projects/1/tasks")
    assert resp.status_code == 403
