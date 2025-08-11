from __future__ import annotations

import sys
from pathlib import Path
from typing import Generator

import jwt
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="function")
def client(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Generator[TestClient, None, None]:
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("JWT_SECRET_KEY", "secret")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("SMTP_HOST", "smtp")
    monkeypatch.setenv("SMTP_PORT", "25")
    monkeypatch.setenv("SMTP_USER", "user")
    monkeypatch.setenv("SMTP_PASSWORD", "pass")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", '["*"]')

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    for key in list(sys.modules):
        if key.startswith("app"):
            sys.modules.pop(key, None)
    from app.database import Base, engine  # noqa: E402
    from app.main import app  # noqa: E402

    Base.metadata.create_all(bind=engine)

    with TestClient(app) as c:
        yield c


def create_token(user_id: str, roles: list[str]) -> str:
    from app.settings import get_settings

    settings = get_settings()
    payload = {"sub": user_id, "roles": roles}
    return jwt.encode(
        payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
