"""Tests for users CRUD endpoints."""

from __future__ import annotations

import pytest

from tests.conftest import auth_headers


@pytest.fixture
async def admin(make_user, tenant):
    return await make_user(tenant_id=tenant.id, role="admin")


@pytest.fixture
async def operator(make_user, tenant):
    return await make_user(tenant_id=tenant.id, role="operator")


@pytest.fixture
async def passenger(make_user, tenant):
    return await make_user(tenant_id=tenant.id, role="passenger")


@pytest.fixture
async def target_user(make_user, tenant):
    return await make_user(
        tenant_id=tenant.id, role="operator", email="target@test.local"
    )


# ---------------------------------------------------------------------------
# GET /users
# ---------------------------------------------------------------------------


async def test_list_returns_200_for_admin(client, admin, target_user):
    r = await client.get("/api/v1/users", headers=auth_headers(admin))
    assert r.status_code == 200
    ids = [u["id"] for u in r.json()["data"]]
    assert target_user.id in ids


async def test_list_returns_401_without_token(client):
    r = await client.get("/api/v1/users")
    assert r.status_code == 401


async def test_list_returns_403_for_passenger(client, passenger):
    r = await client.get("/api/v1/users", headers=auth_headers(passenger))
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# POST /users
# ---------------------------------------------------------------------------


async def test_create_returns_201(client, admin):
    r = await client.post(
        "/api/v1/users",
        json={
            "full_name": "New User",
            "email": "new@test.local",
            "role": "operator",
            "password": "TestPass123!",
        },
        headers=auth_headers(admin),
    )
    assert r.status_code == 201
    assert r.json()["data"]["email"] == "new@test.local"


async def test_create_returns_401_without_token(client):
    r = await client.post(
        "/api/v1/users",
        json={
            "full_name": "X",
            "email": "x@x.com",
            "role": "operator",
            "password": "Pass123!",
        },
    )
    assert r.status_code == 401


async def test_create_returns_403_for_operator(client, operator):
    r = await client.post(
        "/api/v1/users",
        json={
            "full_name": "X",
            "email": "x@x.com",
            "role": "operator",
            "password": "Pass123!",
        },
        headers=auth_headers(operator),
    )
    assert r.status_code == 403


async def test_create_returns_422_missing_fields(client, admin):
    r = await client.post(
        "/api/v1/users", json={"full_name": "X"}, headers=auth_headers(admin)
    )
    assert r.status_code == 422


async def test_create_duplicate_email_returns_409(client, admin, target_user):
    r = await client.post(
        "/api/v1/users",
        json={
            "full_name": "Dup",
            "email": target_user.email,
            "role": "operator",
            "password": "TestPass123!",
        },
        headers=auth_headers(admin),
    )
    assert r.status_code == 409


# ---------------------------------------------------------------------------
# GET /users/{id}
# ---------------------------------------------------------------------------


async def test_get_own_profile(client, operator):
    r = await client.get(f"/api/v1/users/{operator.id}", headers=auth_headers(operator))
    assert r.status_code == 200
    assert r.json()["data"]["id"] == operator.id


async def test_get_returns_401_without_token(client, target_user):
    r = await client.get(f"/api/v1/users/{target_user.id}")
    assert r.status_code == 401


async def test_get_returns_404_unknown(client, admin):
    r = await client.get(
        "/api/v1/users/user-does-not-exist", headers=auth_headers(admin)
    )
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /users/{id}
# ---------------------------------------------------------------------------


async def test_patch_own_profile(client, operator):
    r = await client.patch(
        f"/api/v1/users/{operator.id}",
        json={"full_name": "Updated Name"},
        headers=auth_headers(operator),
    )
    assert r.status_code == 200
    assert r.json()["data"]["fullName"] == "Updated Name"


async def test_patch_returns_401_without_token(client, target_user):
    r = await client.patch(f"/api/v1/users/{target_user.id}", json={"full_name": "X"})
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# DELETE /users/{id}
# ---------------------------------------------------------------------------


async def test_delete_happy_path(client, admin, target_user):
    r = await client.delete(
        f"/api/v1/users/{target_user.id}", headers=auth_headers(admin)
    )
    assert r.status_code == 204


async def test_delete_returns_401_without_token(client, target_user):
    r = await client.delete(f"/api/v1/users/{target_user.id}")
    assert r.status_code == 401


async def test_delete_returns_403_for_operator(client, operator, target_user):
    r = await client.delete(
        f"/api/v1/users/{target_user.id}", headers=auth_headers(operator)
    )
    assert r.status_code == 403
