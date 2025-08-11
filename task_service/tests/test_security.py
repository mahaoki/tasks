from __future__ import annotations

import asyncio
import types

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.security import HTTPAuthorizationCredentials
from jwt.utils import base64url_encode

from task_service.core import security


@pytest.fixture()
def token_and_jwk() -> tuple[str, dict[str, str]]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    numbers = public_key.public_numbers()
    n = base64url_encode(
        numbers.n.to_bytes((numbers.n.bit_length() + 7) // 8, "big")
    ).decode()
    e = base64url_encode(
        numbers.e.to_bytes((numbers.e.bit_length() + 7) // 8, "big")
    ).decode()
    jwk = {"kty": "RSA", "use": "sig", "kid": "test", "alg": "RS256", "n": n, "e": e}
    token = jwt.encode(
        {"sub": "123", "sector_id": 5},
        private_key,
        algorithm="RS256",
        headers={"kid": "test"},
    )
    return token, jwk


def test_validate_token_uses_cache(monkeypatch, token_and_jwk) -> None:
    token, jwk = token_and_jwk
    calls = {"count": 0}

    async def mock_get(self, url):  # type: ignore[override]
        calls["count"] += 1

        class Resp:
            def raise_for_status(self) -> None:  # pragma: no cover - trivial
                pass

            def json(
                self,
            ) -> dict[str, list[dict[str, str]]]:  # pragma: no cover - trivial
                return {"keys": [jwk]}

        return Resp()

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)
    security._jwks_cache.clear()
    asyncio.run(security.validate_token(token))
    asyncio.run(security.validate_token(token))
    assert calls["count"] == 1


def test_jwk_cache_expires(monkeypatch, token_and_jwk) -> None:
    token, jwk = token_and_jwk
    calls = {"count": 0}

    async def mock_get(self, url):  # type: ignore[override]
        calls["count"] += 1

        class Resp:
            def raise_for_status(self) -> None:  # pragma: no cover
                pass

            def json(self) -> dict[str, list[dict[str, str]]]:  # pragma: no cover
                return {"keys": [jwk]}

        return Resp()

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)
    security._jwks_cache.clear()
    monkeypatch.setattr(security, "JWKS_CACHE_TTL_SECONDS", 10)
    current_time = 0.0
    monkeypatch.setattr(
        security, "time", types.SimpleNamespace(time=lambda: current_time)
    )
    asyncio.run(security.validate_token(token))
    current_time = 20.0
    asyncio.run(security.validate_token(token))
    assert calls["count"] == 2


def test_get_current_user(monkeypatch, token_and_jwk) -> None:
    token, jwk = token_and_jwk

    async def mock_get(self, url):  # type: ignore[override]
        class Resp:
            def raise_for_status(self) -> None:  # pragma: no cover
                pass

            def json(self) -> dict[str, list[dict[str, str]]]:  # pragma: no cover
                return {"keys": [jwk]}

        return Resp()

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)
    security._jwks_cache.clear()
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    user = asyncio.run(security.get_current_user(creds))
    assert user["user_id"] == "123"
    assert user["sector_id"] == 5
