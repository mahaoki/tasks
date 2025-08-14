from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest


def test_database_url_options(monkeypatch: pytest.MonkeyPatch) -> None:
    db_url = (
        "postgresql+asyncpg://app:app@localhost:5432/app"
        "?options=-csearch_path%3Dusers"
    )
    monkeypatch.setenv("DATABASE_URL", db_url)

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    for key in list(sys.modules):
        if key.startswith("app"):
            sys.modules.pop(key, None)

    captured: dict[str, object] = {}

    def fake_create_async_engine(url: str, **kwargs):  # type: ignore[no-untyped-def]
        captured["url"] = url
        captured["connect_args"] = kwargs.get("connect_args")

        class Dummy:  # pragma: no cover - simple stub
            pass

        return Dummy()

    def fake_create_engine(url: str, **kwargs):  # type: ignore[no-untyped-def]
        class Dummy:  # pragma: no cover - simple stub
            pass

        return Dummy()

    monkeypatch.setattr(
        "sqlalchemy.ext.asyncio.create_async_engine", fake_create_async_engine
    )
    monkeypatch.setattr("sqlalchemy.create_engine", fake_create_engine)

    import app.database as database

    importlib.reload(database)

    assert captured["url"] == "postgresql+asyncpg://app:app@localhost:5432/app"
    assert captured["connect_args"] == {"server_settings": {"search_path": "users"}}
