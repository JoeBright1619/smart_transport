"""Tests for automatic trip start and departure-delay (start_delay) recording.

Scheduled trips are auto-started by the background dispatcher at ``scheduled_start`` plus a
small, per-trip offset (skewed late) — no manual click needed. Activation records
``start_delay = actual_start − scheduled_start`` so late/early departures are analysable.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.schemas.trip import TripUpdate, classify_delay
from app.services import trip_auto_start, trip_service


@pytest.fixture
async def idle_vehicle(make_vehicle, driver_user, route, tenant):
    return await make_vehicle(
        tenant_id=tenant.id,
        status="idle",
        driver_id=driver_user.id,
        route_id=route.id,
        lat=-1.95,
        lng=30.06,
    )


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def _scheduled_trip(
    db, make_trip, tenant, vehicle, route, driver_user, *, starts_in_min
):
    trip = await make_trip(
        tenant_id=tenant.id,
        vehicle_id=vehicle.id,
        route_id=route.id,
        driver_id=driver_user.id,
        status="scheduled",
    )
    trip.scheduled_start = _now() + timedelta(minutes=starts_in_min)
    trip.scheduled_end = trip.scheduled_start + timedelta(minutes=30)
    await db.flush()
    return trip


# ---------------------------------------------------------------------------
# The per-trip start offset
# ---------------------------------------------------------------------------


def test_start_offset_is_deterministic_and_bounded():
    for i in range(300):
        tid = f"trip-{i}"
        offset = trip_auto_start.start_offset_minutes(tid)
        assert -2 <= offset <= 4
        # Stable across calls — the "is it due yet?" check must not drift each tick.
        assert trip_auto_start.start_offset_minutes(tid) == offset


# ---------------------------------------------------------------------------
# start_delay is recorded on activation
# ---------------------------------------------------------------------------


async def test_activation_records_late_start_delay(
    db, admin_user, tenant, route, driver_user, idle_vehicle, make_trip
):
    trip = await _scheduled_trip(
        db, make_trip, tenant, idle_vehicle, route, driver_user, starts_in_min=-8
    )
    await trip_service.update_trip(
        db, trip.id, TripUpdate(status="active"), tenant.id, admin_user.id
    )
    await db.refresh(trip)
    assert trip.start_delay == pytest.approx(8, abs=1)
    assert classify_delay(trip.start_delay) == "delayed"


async def test_activation_on_time_start_delay(
    db, admin_user, tenant, route, driver_user, idle_vehicle, make_trip
):
    trip = await _scheduled_trip(
        db, make_trip, tenant, idle_vehicle, route, driver_user, starts_in_min=-2
    )
    await trip_service.update_trip(
        db, trip.id, TripUpdate(status="active"), tenant.id, admin_user.id
    )
    await db.refresh(trip)
    assert abs(trip.start_delay) <= 5
    assert classify_delay(trip.start_delay) == "on_time"


# ---------------------------------------------------------------------------
# The auto-start dispatcher
# ---------------------------------------------------------------------------


async def test_auto_start_activates_due_trip(
    db, tenant, route, driver_user, idle_vehicle, make_trip
):
    now = _now()
    trip = await _scheduled_trip(
        db, make_trip, tenant, idle_vehicle, route, driver_user, starts_in_min=-20
    )

    started = await trip_auto_start.auto_start_scheduled_trips(db, now)

    assert trip.id in started
    await db.refresh(trip)
    await db.refresh(idle_vehicle)
    await db.refresh(driver_user)
    assert trip.status == "active"
    assert idle_vehicle.status == "active"
    assert driver_user.status == "on-trip"
    # Scheduled 20 min ago; even the latest offset (+10) leaves it clearly late.
    assert trip.start_delay >= 10


async def test_auto_start_skips_future_trip(
    db, tenant, route, driver_user, idle_vehicle, make_trip
):
    now = _now()
    trip = await _scheduled_trip(
        db, make_trip, tenant, idle_vehicle, route, driver_user, starts_in_min=30
    )

    started = await trip_auto_start.auto_start_scheduled_trips(db, now)

    assert trip.id not in started
    await db.refresh(trip)
    assert trip.status == "scheduled"


async def test_short_window_trip_starts_within_window(
    db, tenant, route, driver_user, idle_vehicle, make_trip
):
    now = _now()
    trip = await make_trip(
        tenant_id=tenant.id,
        vehicle_id=idle_vehicle.id,
        route_id=route.id,
        driver_id=driver_user.id,
        status="scheduled",
    )
    # A 2-minute window that began 2 minutes ago. Without clamping the offset to the
    # window, a late-offset trip would be scheduled to start past its end and never fire.
    trip.scheduled_start = now - timedelta(minutes=2)
    trip.scheduled_end = now
    await db.flush()

    started = await trip_auto_start.auto_start_scheduled_trips(db, now)

    assert trip.id in started


async def test_auto_start_skips_non_idle_vehicle(
    db, tenant, route, driver_user, make_vehicle, make_trip
):
    # A human parked the vehicle in maintenance after the trip was scheduled.
    vehicle = await make_vehicle(
        tenant_id=tenant.id,
        status="maintenance",
        driver_id=driver_user.id,
        route_id=route.id,
    )
    now = _now()
    trip = await _scheduled_trip(
        db, make_trip, tenant, vehicle, route, driver_user, starts_in_min=-20
    )

    started = await trip_auto_start.auto_start_scheduled_trips(db, now)

    assert trip.id not in started
    await db.refresh(trip)
    assert trip.status == "scheduled"
