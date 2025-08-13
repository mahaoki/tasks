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


async def test_users_me_and_sectors_seed(client):
    token = await get_admin_token()
    res = await client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "admin@example.com"
    assert any(s["name"] == "Gerente" for s in data["sectors"])


async def test_get_users_requires_admin_or_manager(client):
    from app import models
    from app.database import async_session_factory

    async with async_session_factory() as db:
        admin = (
            (await db.execute(select(models.User).filter_by(email="admin@example.com")))
            .scalars()
            .first()
        )
        assert admin is not None
    token = create_token(str(admin.id), ["user"])  # not admin or manager
    res = await client.get("/users", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403


async def get_manager_token(client) -> str:
    admin_token = await get_admin_token()
    email = f"manager{uuid.uuid4().hex}@example.com"
    res = await client.post(
        "/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "email": email,
            "full_name": "Manager",
            "roles": ["manager"],
            "sectors": [],
        },
    )
    assert res.status_code == 201
    manager_id = res.json()["id"]
    return create_token(manager_id, ["manager"])


async def test_manager_can_list_and_create_collaborator(client):
    manager_token = await get_manager_token(client)
    res_list = await client.get(
        "/users", headers={"Authorization": f"Bearer {manager_token}"}
    )
    assert res_list.status_code == 200
    res_create = await client.post(
        "/users",
        headers={"Authorization": f"Bearer {manager_token}"},
        json={
            "email": "collab@example.com",
            "full_name": "Collab",
            "roles": ["user"],
            "sectors": [],
        },
    )
    assert res_create.status_code == 201


async def test_manager_cannot_create_admin(client):
    manager_token = await get_manager_token(client)
    res = await client.post(
        "/users",
        headers={"Authorization": f"Bearer {manager_token}"},
        json={
            "email": "badadmin@example.com",
            "full_name": "Bad",
            "roles": ["admin"],
            "sectors": [],
        },
    )
    assert res.status_code == 403


async def test_manager_update_permissions(client):
    admin_token = await get_admin_token()
    manager_token = await get_manager_token(client)
    res_collab = await client.post(
        "/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "email": "tocollab@example.com",
            "full_name": "To Collab",
            "roles": ["user"],
            "sectors": [],
        },
    )
    collab_id = res_collab.json()["id"]
    res_update = await client.patch(
        f"/users/{collab_id}",
        headers={"Authorization": f"Bearer {manager_token}"},
        json={"full_name": "Updated"},
    )
    assert res_update.status_code == 200
    res_promote = await client.patch(
        f"/users/{collab_id}",
        headers={"Authorization": f"Bearer {manager_token}"},
        json={"roles": ["admin"]},
    )
    assert res_promote.status_code == 403
    res_admin = await client.post(
        "/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "email": "otheradmin@example.com",
            "full_name": "Other Admin",
            "roles": ["admin"],
            "sectors": [],
        },
    )
    admin_id = res_admin.json()["id"]
    res_fail = await client.patch(
        f"/users/{admin_id}",
        headers={"Authorization": f"Bearer {manager_token}"},
        json={"full_name": "x"},
    )
    assert res_fail.status_code == 403


async def test_create_and_list_users_with_pagination(client):
    admin_token = await get_admin_token()
    for i in range(3):
        res = await client.post(
            "/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "email": f"user{i}@example.com",
                "full_name": f"User {i}",
                "roles": ["user"],
                "sectors": [],
            },
        )
        assert res.status_code == 201
    res1 = await client.get(
        "/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        params={"page": 1, "page_size": 2},
    )
    res2 = await client.get(
        "/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        params={"page": 2, "page_size": 2},
    )
    assert res1.status_code == 200 and res2.status_code == 200
    assert len(res1.json()) == 2
    assert len(res2.json()) >= 1
    assert res1.json()[0]["id"] != res2.json()[0]["id"]


async def test_patch_user_and_roles_sectors(client):
    admin_token = await get_admin_token()
    res = await client.post(
        "/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "email": "patch@example.com",
            "full_name": "Patch User",
            "roles": [],
            "sectors": [],
        },
    )
    assert res.status_code == 201
    user_id = res.json()["id"]
    res_patch = await client.patch(
        f"/users/{user_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"full_name": "Updated", "roles": ["user"], "sectors": ["Gerente"]},
    )
    assert res_patch.status_code == 200
    data = res_patch.json()
    assert data["full_name"] == "Updated"
    assert any(r["name"] == "user" for r in data["roles"])
    assert any(s["name"] == "Gerente" for s in data["sectors"])
