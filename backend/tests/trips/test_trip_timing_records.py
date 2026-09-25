"""Tests for per-loop trip recording: real passenger counts and signed, route-relative delay.

When a loop completes, the trip records:
  * passengers = everyone who actually boarded during the loop (summed from boarding
    records attributed to that trip), not a random number;
  * delay = signed minutes vs the route's planned duration (positive = late, ~0 = on time,
    negative = early/quick), classified with a tolerance band by ``classify_delay``.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.boarding_record import BoardingRecord
from app.schemas.trip import ON_TIME_TOLERANCE_MIN, classify_delay
from app.websocket.route_trip_records import complete_trip


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def _active_trip(
    make_trip, tenant, vehicle, route, driver_user, *, started_ago_min
):
    now = _now()
    trip = await make_trip(
        tenant_id=tenant.id,
        vehicle_id=vehicle.id,
        route_id=route.id,
        driver_id=driver_user.id,
        status="active",
    )
    trip.actual_start = now - timedelta(minutes=started_ago_min)
    return trip, now


# ---------------------------------------------------------------------------
# Passengers = real boardings
# ---------------------------------------------------------------------------


async def test_passengers_sum_actual_boardings(
    db: AsyncSession, make_trip, tenant, vehicle, route, driver_user
):
    trip, now = await _active_trip(
        make_trip, tenant, vehicle, route, driver_user, started_ago_min=30
    )
    db.add_all(
        [
            BoardingRecord(
                trip_id=trip.id,
                stop_id="s1",
                event_type="boarded",
                count=8,
                recorded_at=now,
                occupancy_after=8,
                tenant_id=tenant.id,
            ),
            BoardingRecord(
                trip_id=trip.id,
                stop_id="s2",
                event_type="boarded",
                count=5,
                recorded_at=now,
                occupancy_after=13,
                tenant_id=tenant.id,
            ),
            # Alightings must not count toward ridership.
            BoardingRecord(
                trip_id=trip.id,
                stop_id="s2",
                event_type="alighted",
                count=4,
                recorded_at=now,
                occupancy_after=9,
                tenant_id=tenant.id,
            ),
        ]
    )
    await db.flush()

    await complete_trip(db, vehicle, {"current_trip_id": trip.id}, now)
    await db.refresh(trip)

    assert trip.status == "completed"
    assert trip.passengers == 13  # 8 + 5 boarded; alighted ignored


async def test_passengers_zero_when_no_boardings(
    db: AsyncSession, make_trip, tenant, vehicle, route, driver_user
):
    trip, now = await _active_trip(
        make_trip, tenant, vehicle, route, driver_user, started_ago_min=30
    )
    await complete_trip(db, vehicle, {"current_trip_id": trip.id}, now)
    await db.refresh(trip)
    assert trip.passengers == 0


# ---------------------------------------------------------------------------
# Delay is signed and measured against the route's planned duration (30 min)
# ---------------------------------------------------------------------------


async def test_delay_positive_when_slower_than_route(
    db: AsyncSession, make_trip, tenant, vehicle, route, driver_user
):
    # Ran 42 min against a 30-min route → ~12 min late.
    trip, now = await _active_trip(
        make_trip, tenant, vehicle, route, driver_user, started_ago_min=42
    )
    await complete_trip(db, vehicle, {"current_trip_id": trip.id}, now)
    await db.refresh(trip)
    assert trip.delay == pytest.approx(12, abs=1)
    assert classify_delay(trip.delay) == "delayed"


async def test_delay_negative_when_faster_than_route(
    db: AsyncSession, make_trip, tenant, vehicle, route, driver_user
):
    # Ran 18 min against a 30-min route → ~12 min early.
    trip, now = await _active_trip(
        make_trip, tenant, vehicle, route, driver_user, started_ago_min=18
    )
    await complete_trip(db, vehicle, {"current_trip_id": trip.id}, now)
    await db.refresh(trip)
    assert trip.delay == pytest.approx(-12, abs=1)
    assert classify_delay(trip.delay) == "quick"


async def test_delay_within_tolerance_is_on_time(
    db: AsyncSession, make_trip, tenant, vehicle, route, driver_user
):
    # Ran 32 min against a 30-min route → +2, inside the tolerance band.
    trip, now = await _active_trip(
        make_trip, tenant, vehicle, route, driver_user, started_ago_min=32
    )
    await complete_trip(db, vehicle, {"current_trip_id": trip.id}, now)
    await db.refresh(trip)
    assert abs(trip.delay) <= ON_TIME_TOLERANCE_MIN
    assert classify_delay(trip.delay) == "on_time"


# ---------------------------------------------------------------------------
# classify_delay tolerance band
# ---------------------------------------------------------------------------


def test_classify_delay_bands():
    tol = ON_TIME_TOLERANCE_MIN
    assert classify_delay(tol + 1) == "delayed"
    assert classify_delay(tol) == "on_time"
    assert classify_delay(0) == "on_time"
    assert classify_delay(-tol) == "on_time"
    assert classify_delay(-tol - 1) == "quick"
