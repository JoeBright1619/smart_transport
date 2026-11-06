"""Auto-start scheduled trips at their due time.

Extracted from simulation_runner.py when the in-process vehicle
simulation was deleted (gps_service Phase 5, Task 5.2). The auto-start
behaviour is unrelated to vehicle movement — it just transitions
scheduled trips to active when their scheduled start + deterministic
offset arrives.

Called periodically from the backend lifespan (`_auto_start_loop`),
matching the interval the old simulation loop used.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.models.trip import Trip
from app.models.vehicle import Vehicle
from app.schemas.trip import TripUpdate
from app.services import trip_service

logger = logging.getLogger(__name__)


def start_offset_minutes(trip_id: str) -> int:
    """A stable, per-trip departure offset (minutes) applied to auto-started trips.

    Derived deterministically from the trip id so the "is it due yet?" check is stable
    across ticks and restarts (re-randomising each tick would never let a trip start).
    Skewed to mirror real buses: mostly on time, sometimes a little late, rarely early.
    Kept small (max +4) so starts stay snappy; genuinely overdue trips (e.g. long past
    their time) still record a large ``start_delay`` because they activate immediately.
    """
    digest = hashlib.sha256(trip_id.encode()).hexdigest()
    h = int(digest[:8], 16) / 0xFFFFFFFF  # in [0, 1]
    if h < 0.10:  # ~10% depart a touch early
        return -2 if h < 0.05 else -1
    if h < 0.70:  # ~60% on time (0..+2 min)
        return round((h - 0.10) / 0.60 * 2)
    return round(3 + (h - 0.70) / 0.30)  # ~30% a little late (+3..+4 min)


async def auto_start_scheduled_trips(db, now: datetime) -> list[str]:
    """Activate every scheduled trip whose (scheduled_start + offset) has arrived.

    This replaces the manual "Start Trip" click for routine operation (the button stays
    as an override). The per-trip offset produces realistic departure-adherence data:
    ``start_delay`` (recorded on activation) captures whether the trip left late/early.
    Returns the ids of the trips started this cycle.
    """
    rows = (
        await db.execute(
            select(
                Trip.id,
                Trip.scheduled_start,
                Trip.scheduled_end,
                Trip.vehicle_id,
                Trip.tenant_id,
            ).where(Trip.status == "scheduled", Trip.is_deleted.is_(False))
        )
    ).all()

    started: list[str] = []
    for trip_id, scheduled_start, scheduled_end, vehicle_id, tenant_id in rows:
        scheduled = scheduled_start
        if scheduled.tzinfo is None:
            scheduled = scheduled.replace(tzinfo=timezone.utc)
        end = scheduled_end
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)

        # Clamp the late offset so a trip never auto-starts past its own scheduled end
        # (matters for short windows); early offsets are left as-is.
        offset = start_offset_minutes(trip_id)
        if offset > 0:
            window_min = max(0.0, (end - scheduled).total_seconds() / 60)
            offset = min(offset, window_min)

        if now < scheduled + timedelta(minutes=offset):
            continue

        # Only start onto a vehicle that is still free — respects a human parking it in
        # maintenance/offline after scheduling.
        vehicle_status = await db.scalar(
            select(Vehicle.status).where(Vehicle.id == vehicle_id)
        )
        if vehicle_status != "idle":
            continue

        try:
            async with db.begin_nested():
                await trip_service.update_trip(
                    db, trip_id, TripUpdate(status="active"), tenant_id, None
                )
            started.append(trip_id)
        except Exception:
            logger.warning("Auto-start failed for trip %s", trip_id, exc_info=True)

    return started
