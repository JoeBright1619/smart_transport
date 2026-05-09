"""Tests for auth endpoints: register, login, refresh, logout."""

from __future__ import annotations


_REGISTER_PAYLOAD = {
    "company_name": "Acme Transit",
    "contact_email": "contact@acme.test",
    "admin_full_name": "Acme Admin",
    "admin_email": "admin@acme.test",
    "password": "SecurePass1!",
}


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------


async def test_register_happy_path(client):
    r = await client.post("/auth/register", json=_REGISTER_PAYLOAD)
    assert r.status_code == 201
    body = r.json()
    assert body["data"]["accessToken"]
    assert body["data"]["user"]["email"] == "admin@acme.test"


async def test_register_duplicate_email_returns_409(client):
    await client.post("/auth/register", json=_REGISTER_PAYLOAD)
    r = await client.post("/auth/register", json=_REGISTER_PAYLOAD)
    assert r.status_code == 409


async def test_register_missing_required_field_returns_422(client):
    payload = {k: v for k, v in _REGISTER_PAYLOAD.items() if k != "password"}
    r = await client.post("/auth/register", json=payload)
    assert r.status_code == 422


async def test_register_short_password_returns_422(client):
    r = await client.post(
        "/auth/register", json={**_REGISTER_PAYLOAD, "password": "short"}
    )
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


async def test_login_happy_path(client, make_tenant, make_user):
    tenant = await make_tenant()
    await make_user(
        tenant_id=tenant.id,
        role="admin",
        email="login@test.local",
        password="TestPass123!",
    )
    r = await client.post(
        "/auth/login", json={"email": "login@test.local", "password": "TestPass123!"}
    )
    assert r.status_code == 200
    assert r.json()["data"]["accessToken"]


async def test_login_wrong_password_returns_401(client, make_tenant, make_user):
    tenant = await make_tenant()
    await make_user(tenant_id=tenant.id, role="admin", email="wrong@test.local")
    r = await client.post(
        "/auth/login", json={"email": "wrong@test.local", "password": "WrongPass999!"}
    )
    assert r.status_code == 401


async def test_login_unknown_email_returns_401(client):
    r = await client.post(
        "/auth/login", json={"email": "nobody@test.local", "password": "TestPass123!"}
    )
    assert r.status_code == 401


async def test_login_missing_field_returns_422(client):
    r = await client.post("/auth/login", json={"email": "x@test.local"})
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Refresh / Logout
# ---------------------------------------------------------------------------


async def test_refresh_after_login(client):
    await client.post("/auth/register", json=_REGISTER_PAYLOAD)
    r = await client.post("/auth/refresh")
    assert r.status_code == 200
    assert r.json()["data"]["accessToken"]


async def test_refresh_without_cookie_returns_401(client):
    r = await client.post("/auth/refresh")
    assert r.status_code == 401


async def test_logout_clears_cookie(client):
    await client.post("/auth/register", json=_REGISTER_PAYLOAD)
    r = await client.post("/auth/logout")
    assert r.status_code == 200
