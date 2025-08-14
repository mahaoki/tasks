from __future__ import annotations

import uuid

import pytest

from .conftest import create_token

pytestmark = pytest.mark.asyncio


async def get_admin_token() -> str:
    from app import models
    from app.database import async_session_factory
    from sqlalchemy import select

    async with async_session_factory() as db:
        admin = (
            (await db.execute(select(models.User).filter_by(email="admin@example.com")))
            .scalars()
            .first()
        )
        assert admin is not None
        return create_token(str(admin.id), ["admin"])


async def test_project_member_crud(client):
    admin_token = await get_admin_token()
    email = f"member{uuid.uuid4().hex}@example.com"
    res_user = await client.post(
        "/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"email": email, "full_name": "Member", "roles": ["user"], "sectors": []},
    )
    assert res_user.status_code == 201
    user_id = res_user.json()["id"]
    project_id = 1

    # create member
    res_put = await client.put(
        f"/projects/{project_id}/members/{user_id}",
        json={"role": "member"},
    )
    assert res_put.status_code == 200
    assert res_put.json() == {"user_id": user_id, "role": "member"}

    # list members
    res_list = await client.get(f"/projects/{project_id}/members")
    assert res_list.status_code == 200
    assert res_list.json() == {"members": [{"user_id": user_id, "role": "member"}]}

    # update member role
    res_put2 = await client.put(
        f"/projects/{project_id}/members/{user_id}",
        json={"role": "owner"},
    )
    assert res_put2.status_code == 200
    assert res_put2.json()["role"] == "owner"

    # delete member
    res_del = await client.delete(f"/projects/{project_id}/members/{user_id}")
    assert res_del.status_code == 204

    # ensure empty list after deletion
    res_list2 = await client.get(f"/projects/{project_id}/members")
    assert res_list2.status_code == 200
    assert res_list2.json() == {"members": []}

    # delete again should return 404
    res_del2 = await client.delete(f"/projects/{project_id}/members/{user_id}")
    assert res_del2.status_code == 404
