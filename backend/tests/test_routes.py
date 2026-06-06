"""Tests for routes CRUD endpoints."""

from __future__ import annotations

import pytest

from tests.conftest import auth_headers

_STOPS = [
    {"name": "Stop A", "lat": -1.95, "lng": 30.06, "order": 1},
    {"name": "Stop B", "lat": -1.94, "lng": 30.07, "order": 2},
]
_CREATE = {
    "name": "Test Route",
    "number": "101",
    "distance": 10.0,
    "duration": 30,
    "color": "#3B82F6",
    "stops": _STOPS,
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
async def passenger(make_user, tenant):
    return await make_user(tenant_id=tenant.id, role="passenger")


@pytest.fixture
async def route(make_route, tenant):
    return await make_route(tenant_id=tenant.id)


# ---------------------------------------------------------------------------
# GET /routes
# ---------------------------------------------------------------------------


async def test_list_returns_200(client, admin, route):
    r = await client.get("/api/v1/routes", headers=auth_headers(admin))
    assert r.status_code == 200
    ids = [x["id"] for x in r.json()["data"]]
    assert route.id in ids


async def test_list_returns_401_without_token(client):
    r = await client.get("/api/v1/routes")
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# POST /routes
# ---------------------------------------------------------------------------


async def test_create_happy_path(client, admin):
    # Routes now reference existing global stops by ID — create them first.
    stop_a = (
        await client.post(
            "/api/v1/stops",
            json={"name": "Stop A", "lat": -1.95, "lng": 30.06},
            headers=auth_headers(admin),
        )
    ).json()["data"]
    stop_b = (
        await client.post(
            "/api/v1/stops",
            json={"name": "Stop B", "lat": -1.94, "lng": 30.07},
            headers=auth_headers(admin),
        )
    ).json()["data"]

    payload = {
        **{k: v for k, v in _CREATE.items() if k != "stops"},
        "stops": [
            {"stopId": stop_a["id"], "order": 1},
            {"stopId": stop_b["id"], "order": 2},
        ],
    }
    r = await client.post("/api/v1/routes", json=payload, headers=auth_headers(admin))
    assert r.status_code == 201
    body = r.json()["data"]
    assert body["name"] == "Test Route"
    assert len(body["stops"]) == 2


async def test_create_returns_401_without_token(client):
    r = await client.post("/api/v1/routes", json=_CREATE)
    assert r.status_code == 401


async def test_create_returns_403_for_passenger(client, passenger):
    r = await client.post(
        "/api/v1/routes", json=_CREATE, headers=auth_headers(passenger)
    )
    assert r.status_code == 403


async def test_create_returns_422_missing_stops(client, admin):
    payload = {k: v for k, v in _CREATE.items() if k != "stops"}
    r = await client.post("/api/v1/routes", json=payload, headers=auth_headers(admin))
    assert r.status_code == 422


async def test_create_returns_422_empty_stops(client, admin):
    r = await client.post(
        "/api/v1/routes", json={**_CREATE, "stops": []}, headers=auth_headers(admin)
    )
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# GET /routes/{id}
# ---------------------------------------------------------------------------


async def test_get_returns_200(client, admin, route):
    r = await client.get(f"/api/v1/routes/{route.id}", headers=auth_headers(admin))
    assert r.status_code == 200
    assert r.json()["data"]["id"] == route.id


async def test_get_returns_401_without_token(client, route):
    r = await client.get(f"/api/v1/routes/{route.id}")
    assert r.status_code == 401


async def test_get_returns_404_unknown(client, admin):
    r = await client.get(
        "/api/v1/routes/route-does-not-exist", headers=auth_headers(admin)
    )
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /routes/{id}
# ---------------------------------------------------------------------------


async def test_patch_happy_path(client, admin, route):
    r = await client.patch(
        f"/api/v1/routes/{route.id}",
        json={"name": "Renamed Route"},
        headers=auth_headers(admin),
    )
    assert r.status_code == 200
    assert r.json()["data"]["name"] == "Renamed Route"


async def test_patch_returns_401_without_token(client, route):
    r = await client.patch(f"/api/v1/routes/{route.id}", json={"name": "X"})
    assert r.status_code == 401


async def test_patch_returns_403_for_passenger(client, passenger, route):
    r = await client.patch(
        f"/api/v1/routes/{route.id}",
        json={"name": "X"},
        headers=auth_headers(passenger),
    )
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# DELETE /routes/{id}
# ---------------------------------------------------------------------------


async def test_delete_happy_path(client, admin, route):
    r = await client.delete(f"/api/v1/routes/{route.id}", headers=auth_headers(admin))
    assert r.status_code == 204
    r2 = await client.get(f"/api/v1/routes/{route.id}", headers=auth_headers(admin))
    assert r2.status_code == 404


async def test_delete_returns_401_without_token(client, route):
    r = await client.delete(f"/api/v1/routes/{route.id}")
    assert r.status_code == 401


async def test_delete_returns_403_for_operator(client, operator, route):
    r = await client.delete(
        f"/api/v1/routes/{route.id}", headers=auth_headers(operator)
    )
    assert r.status_code == 403
