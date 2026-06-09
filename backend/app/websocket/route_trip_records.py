from __future__ import annotations

from datetime import datetime, timedelta
from random import randint
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trip import Trip
from app.models.vehicle import Vehicle


async def start_trip(
    db: AsyncSession, vehicle: Vehicle, state: dict[str, Any], now: datetime
) -> None:
    """Create an active Trip when a vehicle departs the terminal and store its ID
    in state so boarding records created during the loop are linked to it."""
    if vehicle.route_id is None or vehicle.driver_id is None:
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
    """Mark the active trip as completed when the vehicle finishes a route loop."""
    trip_id: str | None = state.get("current_trip_id")
    if trip_id is None:
        return

    trip = await db.scalar(select(Trip).where(Trip.id == trip_id))
    if trip is None:
        return

    started_at = trip.actual_start or now
    actual_duration = (now - started_at).total_seconds() / 60
    scheduled_duration_min = 35
    delay = max(0, int(actual_duration - scheduled_duration_min))
    passenger_upper_bound = max(20, vehicle.capacity)

    trip.actual_end = now
    trip.status = "completed"
    trip.passengers = randint(20, passenger_upper_bound)  # nosec B311
    trip.delay = delay
    trip.updated_at = now
    state["current_trip_id"] = None
