"""Tests for the journey rounds cap — a journey runs N loops, then auto-ends.

Each route loop stays its own Trip row (analytics unchanged); the cap lives on the vehicle
(``planned_loops`` / ``completed_loops``) so it survives a restart, unlike the in-memory
simulation state. When the planned rounds are done the simulation completes the final
loop's trip and stands the vehicle down: idle, driver freed, occupancy cleared.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.route import RouteStop, Stop
from app.models.trip import Trip
from app.schemas.trip import TripCreate, TripUpdate
from app.services import trip_service
from app.websocket import route_simulation

_PUBLISH = "app.websocket.passenger_simulation.manager.publish_to_tenant"


@pytest.fixture
async def tenant(make_tenant):
    return await make_tenant()


@pytest.fixture
async def admin(make_user, tenant):
    return await make_user(tenant_id=tenant.id, role="admin")


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def _route_with_two_stops(db: AsyncSession, make_route, tenant):
    """A two-stop route whose stops are ~20 m apart, so one tick reaches the next stop."""
    route = await make_route(tenant_id=tenant.id)
    s1 = Stop(
        id=f"stop-a-{route.id}",
        tenant_id=tenant.id,
        name="A",
        lat=-1.95,
        lng=30.06,
        is_deleted=False,
    )
    s2 = Stop(
        id=f"stop-b-{route.id}",
        tenant_id=tenant.id,
        name="B",
        lat=-1.95018,  # ~20 m south of s1 → arrival within a single tick
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
    return route, s1, s2


# ---------------------------------------------------------------------------
# Rounds are chosen at dispatch (create_trip) and land on the vehicle
# ---------------------------------------------------------------------------


async def test_dispatch_uses_custom_rounds(
    db, admin, make_route, make_driver, make_vehicle, tenant
):
    route = await make_route(tenant_id=tenant.id)
    driver = await make_driver(tenant_id=tenant.id)
    vehicle = await make_vehicle(
        tenant_id=tenant.id, status="idle", lat=-1.95, lng=30.06
    )
    now = datetime.now(timezone.utc)

    await trip_service.create_trip(
        db,
        TripCreate(
            vehicle_id=vehicle.id,
            route_id=route.id,
            driver_id=driver.id,
            scheduled_start=now,
            scheduled_end=now + timedelta(hours=1),
            planned_loops=3,
        ),
        tenant.id,
        admin.id,
    )

    # The dispatch decision rides on the vehicle (the journey's home).
    assert vehicle.planned_loops == 3


async def test_dispatch_derives_scheduled_end_from_route_and_rounds(
    db, admin, make_route, make_driver, make_vehicle, tenant
):
    # make_route sets a 30-minute duration; 3 rounds -> a 90-minute journey window.
    route = await make_route(tenant_id=tenant.id)
    driver = await make_driver(tenant_id=tenant.id)
    vehicle = await make_vehicle(
        tenant_id=tenant.id, status="idle", lat=-1.95, lng=30.06
    )
    now = datetime.now(timezone.utc)

    trip = await trip_service.create_trip(
        db,
        TripCreate(
            vehicle_id=vehicle.id,
            route_id=route.id,
            driver_id=driver.id,
            scheduled_start=now,
            planned_loops=3,
        ),
        tenant.id,
        admin.id,
    )

    expected_end = now + timedelta(minutes=30 * 3)
    assert abs((trip.scheduled_end - expected_end).total_seconds()) < 5


async def test_fleet_quick_start_defaults_to_five_rounds(
    db, admin, make_route, make_driver, make_vehicle, tenant
):
    # Fleet "Start" doesn't pick a count, so it falls back to the dispatch default.
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

    await trip_service.start_journey(
        db, vehicle=vehicle, tenant_id=tenant.id, current_user_id=admin.id
    )

    assert vehicle.planned_loops == trip_service.DEFAULT_JOURNEY_LOOPS
    assert vehicle.completed_loops == 0


async def test_completing_trip_clears_rounds_counter(
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
    vehicle.completed_loops = 2  # pretend two loops already ran
    await db.flush()

    await trip_service.update_trip(
        db, trip.id, TripUpdate(status="completed"), tenant.id, admin.id
    )

    assert vehicle.status == "idle"
    assert vehicle.planned_loops is None
    assert vehicle.completed_loops == 0


# ---------------------------------------------------------------------------
# The simulation honours the cap
# ---------------------------------------------------------------------------


async def test_journey_auto_ends_after_planned_loops(
    db, make_route, make_driver, make_vehicle, tenant
):
    route, s1, _ = await _route_with_two_stops(db, make_route, tenant)
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
    await db.commit()
    route_simulation.clear_vehicle_state(vehicle.id)

    with patch(_PUBLISH, new=AsyncMock()):
        for _ in range(10):
            await route_simulation.advance_vehicle(db, vehicle, _now())
            if vehicle.status != "active":
                break

    # The one planned round is done → the journey stood the vehicle down.
    assert vehicle.status == "idle"
    assert vehicle.planned_loops is None
    assert vehicle.completed_loops == 0
    assert vehicle.current_occupancy == 0
    await db.refresh(driver)
    assert driver.status == "available"

    # The final loop still recorded a completed trip; nothing is left active.
    completed = (
        await db.scalars(
            select(Trip).where(
                Trip.vehicle_id == vehicle.id, Trip.status == "completed"
            )
        )
    ).all()
    assert len(completed) >= 1
    active = (
        await db.scalars(
            select(Trip).where(Trip.vehicle_id == vehicle.id, Trip.status == "active")
        )
    ).all()
    assert len(active) == 0


async def test_uncapped_journey_keeps_running(
    db, make_route, make_driver, make_vehicle, tenant
):
    route, s1, _ = await _route_with_two_stops(db, make_route, tenant)
    driver = await make_driver(tenant_id=tenant.id, status="on-trip")
    vehicle = await make_vehicle(
        tenant_id=tenant.id,
        status="active",
        route_id=route.id,
        driver_id=driver.id,
        lat=s1.lat,
        lng=s1.lng,
    )
    vehicle.planned_loops = None  # uncapped → loops indefinitely
    vehicle.completed_loops = 0
    await db.commit()
    route_simulation.clear_vehicle_state(vehicle.id)

    with patch(_PUBLISH, new=AsyncMock()):
        await route_simulation.advance_vehicle(db, vehicle, _now())

    # A loop completed, but with no cap the vehicle keeps running.
    assert vehicle.status == "active"
    assert vehicle.completed_loops == 1
