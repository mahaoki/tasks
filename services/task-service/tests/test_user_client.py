from __future__ import annotations

import httpx
import pytest
from fastapi import HTTPException

from app.services.user_client import UserServiceClient

pytestmark = pytest.mark.asyncio


async def test_get_sector_name_success(monkeypatch):
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json={"id": 1, "name": "Sector"})

    transport = httpx.MockTransport(handler)
    original_async_client = httpx.AsyncClient

    def client_factory(*args, **kwargs):
        kwargs["transport"] = transport
        return original_async_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", client_factory)

    client = UserServiceClient(base_url="http://test")
    name1 = await client.get_sector_name(1)
    name2 = await client.get_sector_name(1)
    assert name1 == "Sector"
    assert name2 == "Sector"
    assert calls == 1


async def test_get_sector_name_not_found(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    original_async_client = httpx.AsyncClient

    def client_factory(*args, **kwargs):
        kwargs["transport"] = transport
        return original_async_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", client_factory)

    client = UserServiceClient(base_url="http://test")
    with pytest.raises(HTTPException):
        await client.get_sector_name(1)
