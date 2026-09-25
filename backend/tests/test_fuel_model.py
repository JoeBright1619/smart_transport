"""Tests for the fuel model: fuel draws down over a journey (no per-loop top-up) and the
tank is refilled to 100% at the depot when the journey ends (auto or manual)."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.route import RouteStop, Stop
from app.schemas.trip import TripUpdate
from app.services import trip_service
from app.websocket import route_simulation

_PUBLISH = "app.websocket.passenger_simulation.manager.publish_to_tenant"


@pytest.fixture
async def admin(make_user, tenant):
    return await make_user(tenant_id=tenant.id, role="admin")


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def _route_with_two_stops(db: AsyncSession, make_route, tenant):
    route = await make_route(tenant_id=tenant.id)
    s1 = Stop(
        id=f"stop-f1-{route.id}",
        tenant_id=tenant.id,
        name="A",
        lat=-1.95,
        lng=30.06,
        is_deleted=False,
    )
    s2 = Stop(
        id=f"stop-f2-{route.id}",
        tenant_id=tenant.id,
        name="B",
        lat=-1.95018,
        lng=30.06,
        is_deleted=False,
    )
    db.add_all([s1, s2])
    await db.flush()
    db.add_all(
        [
            RouteStop(route_id=route.id, stop_id=s1.id, stop_order=0),
            RouteStop(route_id=route.id, stop_id=s2.id, stop_order=1),
        ]
    )
    await db.commit()
    route_simulation._route_stops_cache.pop(route.id, None)
    return route, s1


async def test_fuel_does_not_refill_at_terminal(
    db, make_route, make_driver, make_vehicle, tenant
):
    route, s1 = await _route_with_two_stops(db, make_route, tenant)
    driver = await make_driver(tenant_id=tenant.id, status="on-trip")
    vehicle = await make_vehicle(
        tenant_id=tenant.id,
        status="active",
        route_id=route.id,
        driver_id=driver.id,
        lat=s1.lat,
        lng=s1.lng,
    )
    vehicle.planned_loops = None  # uncapped: keep looping, never auto-end/refuel
    vehicle.completed_loops = 0
    vehicle.fuel = 50
    await db.commit()
    route_simulation.clear_vehicle_state(vehicle.id)

    with patch(_PUBLISH, new=AsyncMock()):
        for _ in range(6):  # crosses the terminal at least once
            await route_simulation.advance_vehicle(db, vehicle, _now())

    # Old behaviour reset fuel to 100 at the terminal; it must only ever draw down now.
    assert vehicle.fuel <= 50
    assert vehicle.status == "active"


async def test_completing_journey_refuels_at_depot(
    db, admin, make_route, make_driver, make_vehicle, tenant
):
    route = await make_route(tenant_id=tenant.id)
    driver = await make_driver(tenant_id=tenant.id)
    vehicle = await make_vehicle(
        tenant_id=tenant.id,
        status="idle",
        driver_id=driver.id,
        route_id=route.id,
        lat=-1.95,
        lng=30.06,
    )
    trip = await trip_service.start_journey(
        db, vehicle=vehicle, tenant_id=tenant.id, current_user_id=admin.id
    )
    vehicle.fuel = 20  # ran low during the journey
    await db.flush()

    await trip_service.update_trip(
        db, trip.id, TripUpdate(status="completed"), tenant.id, admin.id
    )

    assert vehicle.fuel == 100


async def test_auto_end_refuels_at_depot(
    db, make_route, make_driver, make_vehicle, tenant
):
    route, s1 = await _route_with_two_stops(db, make_route, tenant)
    driver = await make_driver(tenant_id=tenant.id, status="on-trip")
    vehicle = await make_vehicle(
        tenant_id=tenant.id,
        status="active",
        route_id=route.id,
        driver_id=driver.id,
        lat=s1.lat,
        lng=s1.lng,
    )
    vehicle.planned_loops = 1
    vehicle.completed_loops = 0
    vehicle.fuel = 30
    await db.commit()
    route_simulation.clear_vehicle_state(vehicle.id)

    with patch(_PUBLISH, new=AsyncMock()):
        for _ in range(10):
            await route_simulation.advance_vehicle(db, vehicle, _now())
            if vehicle.status != "active":
                break

    assert vehicle.status == "idle"
    assert vehicle.fuel == 100
