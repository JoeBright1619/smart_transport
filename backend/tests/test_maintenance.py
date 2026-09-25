"""Tests for maintenance CRUD endpoints."""

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
async def dispatcher(make_user, tenant):
    return await make_user(tenant_id=tenant.id, role="dispatcher")


@pytest.fixture
async def vehicle(make_vehicle, tenant):
    return await make_vehicle(tenant_id=tenant.id)


@pytest.fixture
def create_payload(vehicle):
    return {
        "vehicle_id": vehicle.id,
        "type": "routine",
        "description": "Oil change",
        "scheduled_date": "2026-06-01",
        "cost": 50000.0,
    }


# ---------------------------------------------------------------------------
# GET /maintenance
# ---------------------------------------------------------------------------


async def test_list_returns_200(client, admin):
    r = await client.get("/api/v1/maintenance", headers=auth_headers(admin))
    assert r.status_code == 200


async def test_list_returns_401_without_token(client):
    r = await client.get("/api/v1/maintenance")
    assert r.status_code == 401


async def test_list_returns_403_for_dispatcher(client, dispatcher):
    r = await client.get("/api/v1/maintenance", headers=auth_headers(dispatcher))
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# POST /maintenance
# ---------------------------------------------------------------------------


async def test_create_happy_path(client, admin, create_payload):
    r = await client.post(
        "/api/v1/maintenance", json=create_payload, headers=auth_headers(admin)
    )
    assert r.status_code == 201
    body = r.json()["data"]
    assert body["type"] == "routine"
    assert body["status"] == "scheduled"


async def test_create_returns_401_without_token(client, create_payload):
    r = await client.post("/api/v1/maintenance", json=create_payload)
    assert r.status_code == 401


async def test_create_returns_403_for_dispatcher(client, dispatcher, create_payload):
    r = await client.post(
        "/api/v1/maintenance", json=create_payload, headers=auth_headers(dispatcher)
    )
    assert r.status_code == 403


async def test_create_returns_422_negative_cost(client, admin, create_payload):
    r = await client.post(
        "/api/v1/maintenance",
        json={**create_payload, "cost": -1},
        headers=auth_headers(admin),
    )
    assert r.status_code == 422


async def test_create_returns_422_missing_description(client, admin, create_payload):
    payload = {k: v for k, v in create_payload.items() if k != "description"}
    r = await client.post(
        "/api/v1/maintenance", json=payload, headers=auth_headers(admin)
    )
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# GET /maintenance/{id}
# ---------------------------------------------------------------------------


async def test_get_returns_200(client, admin, create_payload):
    create_r = await client.post(
        "/api/v1/maintenance", json=create_payload, headers=auth_headers(admin)
    )
    mid = create_r.json()["data"]["id"]
    r = await client.get(f"/api/v1/maintenance/{mid}", headers=auth_headers(admin))
    assert r.status_code == 200
    assert r.json()["data"]["id"] == mid


async def test_get_returns_401_without_token(client, admin, create_payload):
    create_r = await client.post(
        "/api/v1/maintenance", json=create_payload, headers=auth_headers(admin)
    )
    mid = create_r.json()["data"]["id"]
    r = await client.get(f"/api/v1/maintenance/{mid}")
    assert r.status_code == 401


async def test_get_returns_404_unknown(client, admin):
    r = await client.get(
        "/api/v1/maintenance/maint-does-not-exist", headers=auth_headers(admin)
    )
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /maintenance/{id}
# ---------------------------------------------------------------------------


async def test_patch_complete_sets_status(client, admin, create_payload):
    create_r = await client.post(
        "/api/v1/maintenance", json=create_payload, headers=auth_headers(admin)
    )
    mid = create_r.json()["data"]["id"]
    r = await client.patch(
        f"/api/v1/maintenance/{mid}",
        json={"status": "completed"},
        headers=auth_headers(admin),
    )
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "completed"


async def test_patch_returns_401_without_token(client, admin, create_payload):
    create_r = await client.post(
        "/api/v1/maintenance", json=create_payload, headers=auth_headers(admin)
    )
    mid = create_r.json()["data"]["id"]
    r = await client.patch(f"/api/v1/maintenance/{mid}", json={"status": "completed"})
    assert r.status_code == 401


async def test_patch_returns_403_for_dispatcher(
    client, admin, dispatcher, create_payload
):
    create_r = await client.post(
        "/api/v1/maintenance", json=create_payload, headers=auth_headers(admin)
    )
    mid = create_r.json()["data"]["id"]
    r = await client.patch(
        f"/api/v1/maintenance/{mid}",
        json={"status": "completed"},
        headers=auth_headers(dispatcher),
    )
    assert r.status_code == 403
