from __future__ import annotations

import jwt


def create_token(user_id: str, roles: list[str]) -> str:
    from app.settings import get_settings

    settings = get_settings()
    payload = {"sub": user_id, "roles": roles}
    return jwt.encode(
        payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )


def get_admin_token() -> str:
    from app import models
    from app.database import SessionLocal

    db = SessionLocal()
    admin = db.query(models.User).filter_by(email="admin@example.com").first()
    token = create_token(str(admin.id), ["admin"])
    db.close()
    return token


def test_users_me_and_sectors_seed(client):
    token = get_admin_token()
    res = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "admin@example.com"
    assert any(s["name"] == "Gerente" for s in data["sectors"])


def test_get_users_requires_admin(client):
    from app import models
    from app.database import SessionLocal

    db = SessionLocal()
    admin = db.query(models.User).filter_by(email="admin@example.com").first()
    db.close()
    token = create_token(str(admin.id), ["user"])  # not admin
    res = client.get("/users", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403


def test_create_and_list_users_with_pagination(client):
    admin_token = get_admin_token()
    for i in range(3):
        res = client.post(
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
    res1 = client.get(
        "/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        params={"page": 1, "page_size": 2},
    )
    res2 = client.get(
        "/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        params={"page": 2, "page_size": 2},
    )
    assert res1.status_code == 200 and res2.status_code == 200
    assert len(res1.json()) == 2
    assert len(res2.json()) >= 1
    assert res1.json()[0]["id"] != res2.json()[0]["id"]


def test_patch_user_and_roles_sectors(client):
    admin_token = get_admin_token()
    res = client.post(
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
    res_patch = client.patch(
        f"/users/{user_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"full_name": "Updated", "roles": ["user"], "sectors": ["Gerente"]},
    )
    assert res_patch.status_code == 200
    data = res_patch.json()
    assert data["full_name"] == "Updated"
    assert any(r["name"] == "user" for r in data["roles"])
    assert any(s["name"] == "Gerente" for s in data["sectors"])


def test_roles_and_sectors_endpoints(client):
    admin_token = get_admin_token()
    res_roles = client.get("/roles", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_roles.status_code == 200
    assert any(r["name"] == "admin" for r in res_roles.json())
    res_sectors = client.get(
        "/sectors", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_sectors.status_code == 200
    assert any(s["name"] == "Gerente" for s in res_sectors.json())


def test_pydantic_validation(client):
    admin_token = get_admin_token()
    res = client.post(
        "/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"email": "not-an-email", "full_name": "x"},
    )
    assert res.status_code == 422
