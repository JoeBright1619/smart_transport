"""Tests for arrivals ETA endpoint."""

from __future__ import annotations

import pytest

from app.models.route import RouteStop, Stop
from tests.conftest import auth_headers


@pytest.fixture
async def tenant(make_tenant):
    return await make_tenant()


@pytest.fixture
async def admin(make_user, tenant):
    return await make_user(tenant_id=tenant.id, role="admin")


@pytest.fixture
async def passenger(make_user, tenant):
    return await make_user(tenant_id=tenant.id, role="passenger")


@pytest.fixture
async def stop(db, tenant):
    s = Stop(
        tenant_id=tenant.id,
        name="Test Stop",
        lat=-1.9500,
        lng=30.0588,
        is_deleted=False,
    )
    db.add(s)
    await db.commit()
    return s


@pytest.fixture
async def active_vehicle_at_stop(db, make_vehicle, make_route, tenant, stop):
    route = await make_route(tenant_id=tenant.id)
    db.add(RouteStop(route_id=route.id, stop_id=stop.id, stop_order=1))
    await db.commit()
    vehicle = await make_vehicle(
        tenant_id=tenant.id,
        status="active",
        route_id=route.id,
        lat=-1.9396,
        lng=30.0585,
    )
    # Give the vehicle a speed so ETA can be calculated
    vehicle.speed = 30
    await db.commit()
    return vehicle


# ---------------------------------------------------------------------------
# GET /api/v1/arrivals
# ---------------------------------------------------------------------------


async def test_arrivals_returns_200_with_vehicles(
    client, admin, stop, active_vehicle_at_stop
):
    r = await client.get(
        f"/api/v1/arrivals?stopId={stop.id}", headers=auth_headers(admin)
    )
    assert r.status_code == 200
    assert isinstance(r.json()["data"], list)


async def test_arrivals_returns_200_empty_when_no_active_vehicles(client, admin, stop):
    r = await client.get(
        f"/api/v1/arrivals?stopId={stop.id}", headers=auth_headers(admin)
    )
    assert r.status_code == 200
    assert r.json()["data"] == []


async def test_arrivals_returns_401_without_token(client, stop):
    r = await client.get(f"/api/v1/arrivals?stopId={stop.id}")
    assert r.status_code == 401


async def test_arrivals_returns_422_without_stop_id(client, admin):
    r = await client.get("/api/v1/arrivals", headers=auth_headers(admin))
    assert r.status_code == 422


async def test_arrivals_returns_404_unknown_stop(client, admin):
    r = await client.get(
        "/api/v1/arrivals?stopId=stop-does-not-exist", headers=auth_headers(admin)
    )
    assert r.status_code == 404
