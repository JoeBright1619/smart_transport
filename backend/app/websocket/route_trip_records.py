from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.boarding_record import BoardingRecord
from app.models.driver import Driver
from app.models.route import Route
from app.models.trip import Trip
from app.models.vehicle import Vehicle

# Falls back to this scheduled duration (minutes) only when a route has no duration set.
FALLBACK_SCHEDULED_MIN = 35


async def _route_duration_min(db: AsyncSession, route_id: str | None) -> int:
    """The route's planned duration in minutes, or the fallback if unavailable."""
    if route_id is None:
        return FALLBACK_SCHEDULED_MIN
    duration = await db.scalar(select(Route.duration).where(Route.id == route_id))
    return int(duration) if duration else FALLBACK_SCHEDULED_MIN


async def _open_active_trip(db: AsyncSession, vehicle: Vehicle) -> Trip | None:
    """Return the vehicle's current open (active) trip, if any."""
    return await db.scalar(
        select(Trip)
        .where(
            Trip.vehicle_id == vehicle.id,
            Trip.status == "active",
            Trip.is_deleted.is_(False),
        )
        .order_by(Trip.created_at.desc())
    )


async def start_trip(
    db: AsyncSession, vehicle: Vehicle, state: dict[str, Any], now: datetime
) -> None:
    """Adopt the vehicle's open trip for this loop, or create one only if none exists.

    The journey is started elsewhere (dispatch/Fleet via ``start_journey``), which already
    creates the active trip. Reusing it here — instead of minting a new row every loop —
    keeps exactly one active trip per running vehicle, so Dispatch's active-trips list and
    analytics don't double-count. A new trip is created only when there is no open one
    (e.g. the next loop after the previous trip was completed)."""
    if vehicle.route_id is None or vehicle.driver_id is None:
        return

    existing = await _open_active_trip(db, vehicle)
    if existing is not None:
        state["current_trip_id"] = existing.id
        state.setdefault("trip_started_at", existing.actual_start or now)
        return

    scheduled_duration_min = await _route_duration_min(db, vehicle.route_id)
    trip = Trip(
        tenant_id=vehicle.tenant_id,
        vehicle_id=vehicle.id,
        route_id=vehicle.route_id,
        driver_id=vehicle.driver_id,
        scheduled_start=now,
        actual_start=now,
        scheduled_end=now + timedelta(minutes=scheduled_duration_min),
        status="active",
        passengers=0,
        delay=0,
        is_deleted=False,
        created_at=now,
        updated_at=now,
    )
    db.add(trip)
    await db.flush()
    state["current_trip_id"] = trip.id
    state["trip_started_at"] = now


async def complete_trip(
    db: AsyncSession, vehicle: Vehicle, state: dict[str, Any], now: datetime
) -> None:
    """Mark the owning trip completed when the vehicle finishes a route loop.

    Uses the trip id tracked in state, falling back to the vehicle's open active trip
    (covers the first loop, where the journey's trip was created by dispatch/Fleet and no
    id was stored yet). Driver/vehicle are intentionally NOT reset here: the vehicle keeps
    looping, so a completed loop is not the end of the journey — that reset is owned by
    the dispatch end-of-journey path and by trip reconciliation."""
    trip_id: str | None = state.get("current_trip_id")
    trip: Trip | None = None
    if trip_id is not None:
        trip = await db.scalar(select(Trip).where(Trip.id == trip_id))
    if trip is None or trip.status != "active":
        trip = await _open_active_trip(db, vehicle)
    if trip is None:
        return

    started_at = trip.actual_start or now
    # A timestamp read back from the DB can be tz-naive (e.g. SQLite) while ``now`` is
    # tz-aware; normalise so the subtraction never mixes the two.
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)
    actual_duration = (now - started_at).total_seconds() / 60

    # Delay is signed and measured against the route's own planned duration: positive =
    # late, ~0 = on time, negative = early/quick (see classify_delay's tolerance band).
    scheduled_duration_min = await _route_duration_min(db, trip.route_id)
    delay = round(actual_duration - scheduled_duration_min)

    # Passengers = everyone who actually boarded during this loop, summed from the
    # boarding records attributed to this trip (0 if none — e.g. no stops visited yet).
    boarded = await db.scalar(
        select(func.coalesce(func.sum(BoardingRecord.count), 0)).where(
            BoardingRecord.trip_id == trip.id,
            BoardingRecord.event_type == "boarded",
        )
    )

    trip.actual_end = now
    trip.status = "completed"
    trip.passengers = int(boarded or 0)
    trip.delay = delay
    trip.updated_at = now
    await db.flush()
    state["current_trip_id"] = None


async def end_journey(
    db: AsyncSession, vehicle: Vehicle, state: dict[str, Any], now: datetime
) -> None:
    """Stand a journey down after its planned rounds are complete.

    Completes the final loop's trip (recording its passengers/delay like any other loop),
    then returns the vehicle to idle and frees the driver — mirroring the manual
    end-of-journey reset in ``trip_service.update_trip`` so auto-end (rounds reached) and
    manual completion leave the same clean state. The per-tick simulation state is cleared
    by the caller."""
    await complete_trip(db, vehicle, state, now)

    if vehicle.driver_id is not None:
        driver = await db.scalar(select(Driver).where(Driver.id == vehicle.driver_id))
        if driver is not None:
            if driver.status == "on-trip":
                driver.status = "available"
                driver.total_trips += 1
            driver.vehicle_id = None

    vehicle.status = "idle"
    vehicle.speed = 0
    vehicle.driver_id = None
    vehicle.route_id = None
    vehicle.current_occupancy = 0
    vehicle.planned_loops = None
    vehicle.completed_loops = 0
    # Back at the depot — refuel for the next journey.
    vehicle.fuel = 100
    await db.flush()
