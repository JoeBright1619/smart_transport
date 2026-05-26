from __future__ import annotations

from datetime import datetime, timedelta
from random import randint
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trip import Trip
from app.models.vehicle import Vehicle


async def create_completed_trip(
    db: AsyncSession, vehicle: Vehicle, state: dict[str, Any], now: datetime
) -> None:
    """Create a completed Trip record when a simulated vehicle finishes a route loop."""
    if vehicle.route_id is None or vehicle.driver_id is None:
        return

    started_at = state.get("trip_started_at") or now
    scheduled_duration_min = 35
    scheduled_end = started_at + timedelta(minutes=scheduled_duration_min)
    actual_duration = (now - started_at).total_seconds() / 60
    delay = max(0, int(actual_duration - scheduled_duration_min))
    passenger_upper_bound = max(20, vehicle.capacity)

    db.add(
        Trip(
            tenant_id=vehicle.tenant_id,
            vehicle_id=vehicle.id,
            route_id=vehicle.route_id,
            driver_id=vehicle.driver_id,
            scheduled_start=started_at,
            actual_start=started_at,
            scheduled_end=scheduled_end,
            actual_end=now,
            status="completed",
            passengers=randint(20, passenger_upper_bound),  # nosec B311
            delay=delay,
            is_deleted=False,
            created_at=started_at,
            updated_at=now,
        )
    )
