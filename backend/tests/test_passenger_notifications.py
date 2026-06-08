"""Tests for GET /api/v1/passengers/me/notifications (Task 4.3)."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.route import RouteStop, Stop
from tests.conftest import auth_headers


@pytest.fixture
async def tenant(make_tenant):
    return await make_tenant()


@pytest.fixture
async def stop(db: AsyncSession, tenant):
    s = Stop(
        id="notif-test-stop-01",
        tenant_id=tenant.id,
        name="Notification Test Stop",
        lat=-1.9500,
        lng=30.0588,
        is_deleted=False,
    )
    db.add(s)
    await db.commit()
    return s


@pytest.fixture
async def active_vehicle_at_stop(
    db: AsyncSession, make_vehicle, make_route, tenant, stop
):
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
    vehicle.speed = 30
    await db.commit()
    return vehicle


@pytest.fixture
async def passenger(make_user):
    return await make_user(tenant_id=None, role="passenger")


async def test_notifications_returns_arrivals_for_preferred_stop(
    client, passenger, stop, active_vehicle_at_stop
):
    """Passenger with a favourite stop served by an active vehicle gets a non-empty list."""
    r = await client.patch(
        "/api/v1/passengers/me",
        headers=auth_headers(passenger),
        json={"preferredStops": [stop.id]},
    )
    assert r.status_code == 200

    r = await client.get(
        "/api/v1/passengers/me/notifications",
        headers=auth_headers(passenger),
    )
    assert r.status_code == 200
    data = r.json()["data"]
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["stopName"] == stop.name
    assert len(data[0]["arrivals"]) >= 1


async def test_notifications_empty_when_no_preferred_stops(client, passenger):
    """Passenger with no preferred stops receives an empty list."""
    r = await client.get(
        "/api/v1/passengers/me/notifications",
        headers=auth_headers(passenger),
    )
    assert r.status_code == 200
    assert r.json()["data"] == []


async def test_notifications_requires_passenger_role(client, make_user, make_tenant):
    """Non-passenger users are blocked from the notifications endpoint."""
    tenant = await make_tenant()
    admin = await make_user(tenant_id=tenant.id, role="admin")
    r = await client.get(
        "/api/v1/passengers/me/notifications",
        headers=auth_headers(admin),
    )
    assert r.status_code == 403
