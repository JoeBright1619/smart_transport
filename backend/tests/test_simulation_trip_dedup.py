"""Tests for Task 7.2 — the simulation reuses the owning trip instead of duplicating it.

A running vehicle's journey already has one active trip (created by dispatch/Fleet). The
per-loop simulation must reuse it, keeping exactly one active trip per vehicle, and must
not reset the driver/vehicle when a loop completes (the journey keeps running).
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trip import Trip
from app.websocket.route_trip_records import complete_trip, start_trip


@pytest.fixture
async def tenant(make_tenant):
    return await make_tenant()


@pytest.fixture
async def route(make_route, tenant):
    return await make_route(tenant_id=tenant.id)


@pytest.fixture
async def driver(make_driver, tenant):
    return await make_driver(tenant_id=tenant.id, status="on-trip")


@pytest.fixture
async def vehicle(make_vehicle, driver, route, tenant):
    return await make_vehicle(
        tenant_id=tenant.id,
        status="active",
        driver_id=driver.id,
        route_id=route.id,
        lat=-1.95,
        lng=30.06,
    )


def _now():
    return datetime.now(timezone.utc)


async def _trips(db: AsyncSession, vehicle_id: str, status: str | None = None):
    query = select(Trip).where(Trip.vehicle_id == vehicle_id)
    if status is not None:
        query = query.where(Trip.status == status)
    return (await db.scalars(query)).all()


async def test_start_trip_reuses_existing_open_trip(
    db: AsyncSession, vehicle, route, driver, make_trip, tenant
):
    t0 = await make_trip(
        tenant_id=tenant.id,
        vehicle_id=vehicle.id,
        route_id=route.id,
        driver_id=driver.id,
        status="active",
    )
    state: dict = {}
    await start_trip(db, vehicle, state, _now())

    # No duplicate trip was created; the existing one was adopted.
    assert len(await _trips(db, vehicle.id)) == 1
    assert state["current_trip_id"] == t0.id


async def test_complete_trip_completes_owning_and_keeps_journey_running(
    db: AsyncSession, vehicle, route, driver, make_trip, tenant
):
    t0 = await make_trip(
        tenant_id=tenant.id,
        vehicle_id=vehicle.id,
        route_id=route.id,
        driver_id=driver.id,
        status="active",
    )
    state = {"current_trip_id": t0.id}
    await complete_trip(db, vehicle, state, _now())

    await db.refresh(t0)
    await db.refresh(driver)
    await db.refresh(vehicle)
    assert t0.status == "completed"
    # The loop finished, but the journey continues — no reset.
    assert driver.status == "on-trip"
    assert vehicle.status == "active"
    assert state["current_trip_id"] is None


async def test_complete_trip_falls_back_to_open_trip_without_state(
    db: AsyncSession, vehicle, route, driver, make_trip, tenant
):
    # First loop: the journey's trip exists but no id was stored in state yet.
    t0 = await make_trip(
        tenant_id=tenant.id,
        vehicle_id=vehicle.id,
        route_id=route.id,
        driver_id=driver.id,
        status="active",
    )
    await complete_trip(db, vehicle, {}, _now())
    await db.refresh(t0)
    assert t0.status == "completed"


async def test_full_loop_then_fresh_next_loop_never_two_active(
    db: AsyncSession, vehicle, route, driver, make_trip, tenant
):
    await make_trip(
        tenant_id=tenant.id,
        vehicle_id=vehicle.id,
        route_id=route.id,
        driver_id=driver.id,
        status="active",
    )
    state: dict = {}

    # Loop 1 — adopt the existing trip and complete it.
    await start_trip(db, vehicle, state, _now())
    await complete_trip(db, vehicle, state, _now())
    assert len(await _trips(db, vehicle.id, status="active")) == 0
    assert len(await _trips(db, vehicle.id, status="completed")) == 1

    # Loop 2 — no open trip now, so exactly one fresh trip is created.
    await start_trip(db, vehicle, state, _now())
    assert len(await _trips(db, vehicle.id, status="active")) == 1
    assert len(await _trips(db, vehicle.id)) == 2  # one completed + one active
