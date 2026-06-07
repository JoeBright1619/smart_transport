"""Tests for cross-tenant public stops and arrivals endpoints."""

from __future__ import annotations

import pytest

from app.models.route import Route, RouteStop, Stop
from tests.conftest import auth_headers


@pytest.fixture
async def tenant_a(make_tenant):
    return await make_tenant(name="Kigali Bus Co.")


@pytest.fixture
async def tenant_b(make_tenant):
    return await make_tenant(name="Nyabugogo Express")


@pytest.fixture
async def passenger_a(make_user, tenant_a):
    return await make_user(tenant_id=None, role="passenger")


@pytest.fixture
async def shared_stop(db, tenant_a):
    stop = Stop(
        tenant_id=tenant_a.id,
        name="Central Market",
        lat=-1.9500,
        lng=30.0588,
        is_deleted=False,
    )
    db.add(stop)
    await db.commit()
    return stop


@pytest.fixture
async def active_vehicle_tenant_a(db, make_vehicle, tenant_a, shared_stop):
    route = Route(
        id=f"route-a-{id(tenant_a)}",
        tenant_id=tenant_a.id,
        name="Route A",
        number="101",
        distance=10.0,
        duration=30,
        is_active=True,
        color="#FF0000",
        is_deleted=False,
    )
    db.add(route)
    await db.flush()
    db.add(RouteStop(route_id=route.id, stop_id=shared_stop.id, stop_order=1))
    await db.flush()
    vehicle = await make_vehicle(
        tenant_id=tenant_a.id,
        status="active",
        route_id=route.id,
        lat=-1.9396,
        lng=30.0585,
    )
    vehicle.speed = 30
    await db.commit()
    return vehicle


@pytest.fixture
async def active_vehicle_tenant_b(db, make_vehicle, tenant_b, shared_stop):
    route = Route(
        id=f"route-b-{id(tenant_b)}",
        tenant_id=tenant_b.id,
        name="Route B",
        number="202",
        distance=8.0,
        duration=25,
        is_active=True,
        color="#0000FF",
        is_deleted=False,
    )
    db.add(route)
    await db.flush()
    db.add(RouteStop(route_id=route.id, stop_id=shared_stop.id, stop_order=1))
    await db.flush()
    vehicle = await make_vehicle(
        tenant_id=tenant_b.id,
        status="active",
        route_id=route.id,
        lat=-1.9450,
        lng=30.0560,
    )
    vehicle.speed = 25
    await db.commit()
    return vehicle


# ---------------------------------------------------------------------------
# GET /api/v1/stops/public
# ---------------------------------------------------------------------------


async def test_public_stops_returns_all_stops_without_auth(client, shared_stop):
    r = await client.get("/api/v1/stops/public")
    assert r.status_code == 200
    ids = [s["id"] for s in r.json()["data"]]
    assert shared_stop.id in ids


async def test_public_stops_returns_200_with_no_stops(client):
    r = await client.get("/api/v1/stops/public")
    assert r.status_code == 200
    assert isinstance(r.json()["data"], list)


# ---------------------------------------------------------------------------
# GET /api/v1/arrivals/public
# ---------------------------------------------------------------------------


async def test_public_arrivals_returns_results_from_multiple_tenants(
    client,
    passenger_a,
    shared_stop,
    active_vehicle_tenant_a,
    active_vehicle_tenant_b,
):
    r = await client.get(
        f"/api/v1/arrivals/public?stop_id={shared_stop.id}",
        headers=auth_headers(passenger_a),
    )
    assert r.status_code == 200
    data = r.json()["data"]
    tenant_names = {item["tenantName"] for item in data}
    assert (
        len(tenant_names) >= 2
    ), f"Expected arrivals from ≥2 tenants, got: {tenant_names}"


async def test_public_arrivals_returns_404_for_unknown_stop(client, passenger_a):
    r = await client.get(
        "/api/v1/arrivals/public?stop_id=stop-does-not-exist",
        headers=auth_headers(passenger_a),
    )
    assert r.status_code == 404
