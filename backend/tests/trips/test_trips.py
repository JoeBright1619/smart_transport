"""Tests for trips CRUD endpoints."""

from __future__ import annotations

import pytest

from tests.conftest import auth_headers


@pytest.fixture
def trip_payload(vehicle, route, driver_user):
    return {
        "vehicle_id": vehicle.id,
        "route_id": route.id,
        "driver_id": driver_user.id,
        "scheduled_start": "2026-06-01T08:00:00Z",
        "scheduled_end": "2026-06-01T10:00:00Z",
    }


# ---------------------------------------------------------------------------
# GET /trips
# ---------------------------------------------------------------------------


async def test_list_returns_200(client, admin_user):
    r = await client.get("/api/v1/trips", headers=auth_headers(admin_user))
    assert r.status_code == 200


async def test_list_returns_401_without_token(client):
    r = await client.get("/api/v1/trips")
    assert r.status_code == 401


async def test_list_returns_403_for_passenger(client, passenger_user):
    r = await client.get("/api/v1/trips", headers=auth_headers(passenger_user))
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# POST /trips
# ---------------------------------------------------------------------------


async def test_create_happy_path(client, admin_user, trip_payload):
    r = await client.post(
        "/api/v1/trips", json=trip_payload, headers=auth_headers(admin_user)
    )
    assert r.status_code == 201
    assert r.json()["data"]["status"] == "scheduled"


async def test_create_returns_401_without_token(client, trip_payload):
    r = await client.post("/api/v1/trips", json=trip_payload)
    assert r.status_code == 401


async def test_create_returns_403_for_operator(client, operator_user, trip_payload):
    r = await client.post(
        "/api/v1/trips", json=trip_payload, headers=auth_headers(operator_user)
    )
    assert r.status_code == 403


async def test_create_returns_422_missing_field(client, admin_user, vehicle, route):
    r = await client.post(
        "/api/v1/trips",
        json={
            "vehicle_id": vehicle.id,
            "route_id": route.id,
            "scheduled_start": "2026-06-01T08:00:00Z",
            "scheduled_end": "2026-06-01T10:00:00Z",
        },
        headers=auth_headers(admin_user),
    )
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# GET /trips/{id}
# ---------------------------------------------------------------------------


async def test_get_returns_200(client, admin_user, trip_payload):
    create_r = await client.post(
        "/api/v1/trips", json=trip_payload, headers=auth_headers(admin_user)
    )
    trip_id = create_r.json()["data"]["id"]
    r = await client.get(f"/api/v1/trips/{trip_id}", headers=auth_headers(admin_user))
    assert r.status_code == 200
    assert r.json()["data"]["id"] == trip_id


async def test_get_returns_401_without_token(client, admin_user, trip_payload):
    create_r = await client.post(
        "/api/v1/trips", json=trip_payload, headers=auth_headers(admin_user)
    )
    trip_id = create_r.json()["data"]["id"]
    r = await client.get(f"/api/v1/trips/{trip_id}")
    assert r.status_code == 401


async def test_get_returns_404_unknown(client, admin_user):
    r = await client.get(
        "/api/v1/trips/trip-does-not-exist", headers=auth_headers(admin_user)
    )
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /trips/{id} — status transitions
# ---------------------------------------------------------------------------


async def test_patch_to_active(client, admin_user, trip_payload):
    create_r = await client.post(
        "/api/v1/trips", json=trip_payload, headers=auth_headers(admin_user)
    )
    trip_id = create_r.json()["data"]["id"]
    r = await client.patch(
        f"/api/v1/trips/{trip_id}",
        json={"status": "active"},
        headers=auth_headers(admin_user),
    )
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "active"


async def test_patch_returns_401_without_token(client, admin_user, trip_payload):
    create_r = await client.post(
        "/api/v1/trips", json=trip_payload, headers=auth_headers(admin_user)
    )
    trip_id = create_r.json()["data"]["id"]
    r = await client.patch(f"/api/v1/trips/{trip_id}", json={"status": "active"})
    assert r.status_code == 401


async def test_patch_returns_403_for_operator(
    client, admin_user, operator_user, trip_payload
):
    create_r = await client.post(
        "/api/v1/trips", json=trip_payload, headers=auth_headers(admin_user)
    )
    trip_id = create_r.json()["data"]["id"]
    r = await client.patch(
        f"/api/v1/trips/{trip_id}",
        json={"status": "active"},
        headers=auth_headers(operator_user),
    )
    assert r.status_code == 403


async def test_patch_invalid_status_transition_returns_400(
    client, admin_user, trip_payload
):
    create_r = await client.post(
        "/api/v1/trips", json=trip_payload, headers=auth_headers(admin_user)
    )
    trip_id = create_r.json()["data"]["id"]
    # scheduled → completed is not a valid transition (must go through active)
    r = await client.patch(
        f"/api/v1/trips/{trip_id}",
        json={"status": "completed"},
        headers=auth_headers(admin_user),
    )
    assert r.status_code == 400
