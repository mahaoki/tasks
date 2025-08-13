from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_healthz(client):
    res = await client.get("/healthz")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}
