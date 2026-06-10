"""Tests for vehicles CRUD endpoints."""

from __future__ import annotations

import pytest

from tests.conftest import auth_headers

_CREATE = {
    "registration_number": "RAD 999 Z",
    "model": "Test Bus",
}


@pytest.fixture
async def tenant(make_tenant):
    return await make_tenant()


@pytest.fixture
async def admin(make_user, tenant):
    return await make_user(tenant_id=tenant.id, role="admin")


@pytest.fixture
async def operator(make_user, tenant):
    return await make_user(tenant_id=tenant.id, role="operator")


@pytest.fixture
async def dispatcher(make_user, tenant):
    return await make_user(tenant_id=tenant.id, role="dispatcher")


@pytest.fixture
async def passenger(make_user, tenant):
    return await make_user(tenant_id=tenant.id, role="passenger")


@pytest.fixture
async def vehicle(make_vehicle, tenant):
    return await make_vehicle(tenant_id=tenant.id)


# ---------------------------------------------------------------------------
# GET /vehicles
# ---------------------------------------------------------------------------


async def test_list_returns_200_for_admin(client, admin, vehicle):
    r = await client.get("/api/v1/vehicles", headers=auth_headers(admin))
    assert r.status_code == 200
    ids = [v["id"] for v in r.json()["data"]]
    assert vehicle.id in ids


async def test_list_returns_401_without_token(client):
    r = await client.get("/api/v1/vehicles")
    assert r.status_code == 401


async def test_list_returns_403_for_passenger(client, passenger):
    r = await client.get("/api/v1/vehicles", headers=auth_headers(passenger))
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# POST /vehicles
# ---------------------------------------------------------------------------


async def test_create_happy_path(client, admin):
    r = await client.post("/api/v1/vehicles", json=_CREATE, headers=auth_headers(admin))
    assert r.status_code == 201
    assert r.json()["data"]["registrationNumber"] == "RAD 999 Z"


async def test_create_returns_401_without_token(client):
    r = await client.post("/api/v1/vehicles", json=_CREATE)
    assert r.status_code == 401


async def test_create_returns_403_for_dispatcher(client, dispatcher):
    r = await client.post(
        "/api/v1/vehicles", json=_CREATE, headers=auth_headers(dispatcher)
    )
    assert r.status_code == 403


async def test_create_returns_422_missing_field(client, admin):
    r = await client.post(
        "/api/v1/vehicles", json={"model": "Bus"}, headers=auth_headers(admin)
    )
    assert r.status_code == 422


async def test_create_returns_422_invalid_seating_capacity(client, admin):
    r = await client.post(
        "/api/v1/vehicles",
        json={**_CREATE, "seating_capacity": 0},
        headers=auth_headers(admin),
    )
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# GET /vehicles/{id}
# ---------------------------------------------------------------------------


async def test_get_returns_200(client, admin, vehicle):
    r = await client.get(f"/api/v1/vehicles/{vehicle.id}", headers=auth_headers(admin))
    assert r.status_code == 200
    assert r.json()["data"]["id"] == vehicle.id


async def test_get_returns_401_without_token(client, vehicle):
    r = await client.get(f"/api/v1/vehicles/{vehicle.id}")
    assert r.status_code == 401


async def test_get_returns_404_unknown_id(client, admin):
    r = await client.get(
        "/api/v1/vehicles/veh-does-not-exist", headers=auth_headers(admin)
    )
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /vehicles/{id}
# ---------------------------------------------------------------------------


async def test_patch_happy_path(client, admin, vehicle):
    r = await client.patch(
        f"/api/v1/vehicles/{vehicle.id}",
        json={"fuel": 75},
        headers=auth_headers(admin),
    )
    assert r.status_code == 200
    assert r.json()["data"]["fuel"] == 75


async def test_patch_returns_401_without_token(client, vehicle):
    r = await client.patch(f"/api/v1/vehicles/{vehicle.id}", json={"fuel": 50})
    assert r.status_code == 401


async def test_patch_returns_403_for_dispatcher(client, dispatcher, vehicle):
    r = await client.patch(
        f"/api/v1/vehicles/{vehicle.id}",
        json={"fuel": 50},
        headers=auth_headers(dispatcher),
    )
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# DELETE /vehicles/{id}
# ---------------------------------------------------------------------------


async def test_delete_happy_path(client, admin, vehicle):
    r = await client.delete(
        f"/api/v1/vehicles/{vehicle.id}", headers=auth_headers(admin)
    )
    assert r.status_code == 204
    r2 = await client.get(f"/api/v1/vehicles/{vehicle.id}", headers=auth_headers(admin))
    assert r2.status_code == 404


async def test_delete_returns_401_without_token(client, vehicle):
    r = await client.delete(f"/api/v1/vehicles/{vehicle.id}")
    assert r.status_code == 401


async def test_delete_returns_403_for_operator(client, operator, vehicle):
    r = await client.delete(
        f"/api/v1/vehicles/{vehicle.id}", headers=auth_headers(operator)
    )
    assert r.status_code == 403


async def test_delete_active_vehicle_returns_409(client, admin, make_vehicle, tenant):
    active = await make_vehicle(tenant_id=tenant.id, status="active")
    r = await client.delete(
        f"/api/v1/vehicles/{active.id}", headers=auth_headers(admin)
    )
    assert r.status_code == 409
