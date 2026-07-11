from __future__ import annotations

from datetime import datetime, timedelta
from random import randint
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trip import Trip
from app.models.vehicle import Vehicle


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

    scheduled_duration_min = 35
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
    actual_duration = (now - started_at).total_seconds() / 60
    scheduled_duration_min = 35
    delay = max(0, int(actual_duration - scheduled_duration_min))
    passenger_upper_bound = max(20, vehicle.seating_capacity)

    trip.actual_end = now
    trip.status = "completed"
    trip.passengers = randint(20, passenger_upper_bound)  # nosec B311
    trip.delay = delay
    trip.updated_at = now
    await db.flush()
    state["current_trip_id"] = None
