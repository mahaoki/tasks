from __future__ import annotations


def test_register_login_me_flow(client) -> None:
    resp = client.post("/auth/register", json={"email": "user@example.com", "password": "secret"})
    assert resp.status_code == 201
    user_id = resp.json()["id"]

    resp = client.post("/auth/login", json={"email": "user@example.com", "password": "secret"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    access = data["access_token"]
    refresh = data["refresh_token"]

    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {access}"})
    assert resp.status_code == 200
    me = resp.json()
    assert me["email"] == "user@example.com"
    assert me["id"] == user_id

    resp = client.post("/auth/refresh", json={"refresh_token": refresh})
    assert resp.status_code == 200
    assert resp.json()["access_token"]

