from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select

from .conftest import create_token

pytestmark = pytest.mark.asyncio


async def get_admin_token() -> str:
    from app import models
    from app.database import async_session_factory

    async with async_session_factory() as db:
        admin = (
            (await db.execute(select(models.User).filter_by(email="admin@example.com")))
            .scalars()
            .first()
        )
        assert admin is not None
        return create_token(str(admin.id), ["admin"])


async def test_get_sector(client):
    token = await get_admin_token()
    res_list = await client.get("/sectors", headers={"Authorization": f"Bearer {token}"})
    assert res_list.status_code == 200
    sectors = res_list.json()
    assert sectors
    sector_id = sectors[0]["id"]
    res = await client.get(
        f"/sectors/{sector_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == sector_id
    assert data["name"] == sectors[0]["name"]


async def test_get_sector_not_found(client):
    token = await get_admin_token()
    res = await client.get(
        f"/sectors/{uuid.uuid4()}", headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 404
