from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

# ruff: noqa: E402


os.environ["TASKS_DATABASE_URL"] = "sqlite+aiosqlite://"

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import get_session
from app.main import app
from app.services import TaskService

sys.path.pop(0)


@pytest.fixture(autouse=True)
def override_session() -> None:
    async def _override_session():
        class Dummy:  # pragma: no cover - placeholder
            pass

        yield Dummy()

    app.dependency_overrides[get_session] = _override_session
    yield
    app.dependency_overrides.clear()


def test_healthz() -> None:
    client = TestClient(app)
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_metrics(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_count_by_status(
        self, session, project_id=None  # type: ignore[override]
    ) -> dict[str, int]:
        return {"pending": 1}

    monkeypatch.setattr(TaskService, "count_by_status", fake_count_by_status)
    client = TestClient(app)
    client.get("/healthz")
    resp = client.get("/metrics")
    assert resp.status_code == 200
    body = resp.text
    assert "http_requests_total" in body
    assert 'path="/healthz"' in body
    assert 'tasks_status_total{status="pending"} 1.0' in body
