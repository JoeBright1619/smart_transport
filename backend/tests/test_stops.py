"""Tests for global stop update and delete endpoints."""

from __future__ import annotations

import pytest

from tests.conftest import auth_headers


@pytest.fixture
async def admin(make_user, tenant):
    return await make_user(tenant_id=tenant.id, role="admin")


@pytest.fixture
async def passenger(make_user, tenant):
    return await make_user(tenant_id=tenant.id, role="passenger")


async def _create_stop(client, admin, *, name, lat, lng):
    r = await client.post(
        "/api/v1/stops",
        json={"name": name, "lat": lat, "lng": lng},
        headers=auth_headers(admin),
    )
    assert r.status_code == 201
    return r.json()["data"]


# ---------------------------------------------------------------------------
# PATCH /stops/{id}
# ---------------------------------------------------------------------------


async def test_update_renames_and_moves(client, admin):
    stop = await _create_stop(client, admin, name="Old", lat=-1.95, lng=30.06)
    r = await client.patch(
        f"/api/v1/stops/{stop['id']}",
        json={"name": "New", "lat": -1.90, "lng": 30.10},
        headers=auth_headers(admin),
    )
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["name"] == "New"
    assert data["lat"] == -1.90
    assert data["lng"] == 30.10


async def test_update_partial_keeps_other_fields(client, admin):
    stop = await _create_stop(client, admin, name="Keep", lat=-1.95, lng=30.06)
    r = await client.patch(
        f"/api/v1/stops/{stop['id']}",
        json={"name": "Renamed"},
        headers=auth_headers(admin),
    )
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["name"] == "Renamed"
    assert data["lat"] == -1.95  # unchanged


async def test_update_name_clash_returns_409(client, admin):
    await _create_stop(client, admin, name="Alpha", lat=-1.95, lng=30.06)
    other = await _create_stop(client, admin, name="Beta", lat=-1.80, lng=30.20)
    r = await client.patch(
        f"/api/v1/stops/{other['id']}",
        json={"name": "Alpha"},
        headers=auth_headers(admin),
    )
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "STOP_NAME_CONFLICT"


async def test_update_coordinate_clash_returns_409(client, admin):
    await _create_stop(client, admin, name="Alpha", lat=-1.95, lng=30.06)
    other = await _create_stop(client, admin, name="Beta", lat=-1.80, lng=30.20)
    r = await client.patch(
        f"/api/v1/stops/{other['id']}",
        json={"lat": -1.95, "lng": 30.06},  # right on top of Alpha
        headers=auth_headers(admin),
    )
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "STOP_COORDINATE_CONFLICT"


async def test_update_same_stop_same_coords_ok(client, admin):
    # Editing a stop must not conflict with itself.
    stop = await _create_stop(client, admin, name="Solo", lat=-1.95, lng=30.06)
    r = await client.patch(
        f"/api/v1/stops/{stop['id']}",
        json={"name": "Solo Renamed", "lat": -1.95, "lng": 30.06},
        headers=auth_headers(admin),
    )
    assert r.status_code == 200


async def test_update_unknown_returns_404(client, admin):
    r = await client.patch(
        "/api/v1/stops/stop-nope",
        json={"name": "X"},
        headers=auth_headers(admin),
    )
    assert r.status_code == 404


async def test_update_returns_403_for_passenger(client, admin, passenger):
    stop = await _create_stop(client, admin, name="Guard", lat=-1.95, lng=30.06)
    r = await client.patch(
        f"/api/v1/stops/{stop['id']}",
        json={"name": "Nope"},
        headers=auth_headers(passenger),
    )
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# DELETE /stops/{id}
# ---------------------------------------------------------------------------


async def test_delete_happy_path(client, admin):
    stop = await _create_stop(client, admin, name="Temp", lat=-1.95, lng=30.06)
    r = await client.delete(f"/api/v1/stops/{stop['id']}", headers=auth_headers(admin))
    assert r.status_code == 204

    listed = await client.get("/api/v1/stops", headers=auth_headers(admin))
    ids = [s["id"] for s in listed.json()["data"]]
    assert stop["id"] not in ids


async def test_delete_in_use_returns_409(client, admin):
    stop_a = await _create_stop(client, admin, name="On Route A", lat=-1.95, lng=30.06)
    stop_b = await _create_stop(client, admin, name="On Route B", lat=-1.94, lng=30.07)
    created = await client.post(
        "/api/v1/routes",
        json={
            "name": "R1",
            "number": "R1",
            "distance": 10.0,
            "duration": 30,
            "color": "#3B82F6",
            "stops": [
                {"stopId": stop_a["id"], "order": 1},
                {"stopId": stop_b["id"], "order": 2},
            ],
        },
        headers=auth_headers(admin),
    )
    assert created.status_code == 201

    r = await client.delete(
        f"/api/v1/stops/{stop_a['id']}", headers=auth_headers(admin)
    )
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "STOP_IN_USE"


async def test_delete_unknown_returns_404(client, admin):
    r = await client.delete("/api/v1/stops/stop-nope", headers=auth_headers(admin))
    assert r.status_code == 404


async def test_delete_returns_403_for_passenger(client, admin, passenger):
    stop = await _create_stop(client, admin, name="Guarded", lat=-1.95, lng=30.06)
    r = await client.delete(
        f"/api/v1/stops/{stop['id']}", headers=auth_headers(passenger)
    )
    assert r.status_code == 403
