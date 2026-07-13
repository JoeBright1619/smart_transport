from __future__ import annotations

import asyncio
import hashlib
import logging
from collections import defaultdict
from contextlib import suppress
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.crud.analytics import upsert_daily_analytics
from app.models.alert import Alert
from app.models.telemetry import Telemetry
from app.models.trip import Trip
from app.models.vehicle import Vehicle
from app.schemas.trip import TripUpdate
from app.services import trip_service
from app.websocket.route_simulation import (
    LOW_FUEL_THRESHOLD,
    TICK_SECONDS,
    advance_vehicle,
)

logger = logging.getLogger(__name__)
_simulation_task: asyncio.Task[None] | None = None


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


def start_vehicle_simulation() -> None:
    """Start the process-wide background vehicle simulation loop."""
    global _simulation_task
    if _simulation_task is None or _simulation_task.done():
        _simulation_task = asyncio.create_task(_simulation_loop())


async def stop_vehicle_simulation() -> None:
    """Stop the background vehicle simulation loop."""
    if _simulation_task is None:
        return

    _simulation_task.cancel()
    with suppress(asyncio.CancelledError):
        await _simulation_task


async def _simulation_loop() -> None:
    while True:
        try:
            await _auto_start_cycle()
            await simulate_active_vehicles()
        except Exception:
            logger.warning("Vehicle simulation cycle failed", exc_info=True)

        await asyncio.sleep(TICK_SECONDS)


async def _auto_start_cycle() -> None:
    """Open a session and auto-start any scheduled trips that are due."""
    now = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as db:
        try:
            await auto_start_scheduled_trips(db, now)
            await db.commit()
        except Exception:
            await db.rollback()
            logger.warning("Auto-start cycle failed", exc_info=True)


async def simulate_active_vehicles() -> None:
    """Advance all active vehicles and persist telemetry for the new positions."""
    timestamp = datetime.now(timezone.utc)

    async with AsyncSessionLocal() as db:
        fuel_drops_by_tenant: dict[str, float] = defaultdict(float)
        vehicles = (
            await db.scalars(
                select(Vehicle).where(
                    Vehicle.is_deleted.is_(False),
                    Vehicle.status == "active",
                    Vehicle.lat.is_not(None),
                    Vehicle.lng.is_not(None),
                )
            )
        ).all()

        for vehicle in vehicles:
            prev_fuel_before = vehicle.fuel or 100
            updates = await advance_vehicle(db, vehicle, timestamp)
            if updates is None:
                continue

            fuel_drops_by_tenant[vehicle.tenant_id] += updates.get("fuel_drop", 0.0)

            vehicle.lat = updates["lat"]
            vehicle.lng = updates["lng"]
            vehicle.speed = updates["speed"]
            vehicle.heading = updates["heading"]
            vehicle.fuel = updates["fuel"]

            db.add(
                Telemetry(
                    tenant_id=vehicle.tenant_id,
                    vehicle_id=vehicle.id,
                    lat=vehicle.lat,
                    lng=vehicle.lng,
                    speed=vehicle.speed or 0,
                    heading=vehicle.heading or 0,
                    timestamp=timestamp,
                )
            )

            if (
                updates.get("fuel", 100) < LOW_FUEL_THRESHOLD
                and prev_fuel_before >= LOW_FUEL_THRESHOLD
            ):
                db.add(
                    Alert(
                        tenant_id=vehicle.tenant_id,
                        type="maintenance",
                        severity="high",
                        title=f"Low Fuel: {vehicle.registration_number}",
                        message=(
                            f"{vehicle.registration_number} fuel is below "
                            f"{LOW_FUEL_THRESHOLD}%."
                        ),
                        vehicle_id=vehicle.id,
                        is_acknowledged=False,
                    )
                )

            # A vehicle stuck in traffic long enough raises a delay alert (once per
            # journey; suppressed if one is already open for the vehicle).
            if updates.get("delay_crossed"):
                open_delay = await db.scalar(
                    select(Alert.id).where(
                        Alert.tenant_id == vehicle.tenant_id,
                        Alert.type == "delay",
                        Alert.vehicle_id == vehicle.id,
                        Alert.is_acknowledged.is_(False),
                    )
                )
                if open_delay is None:
                    db.add(
                        Alert(
                            tenant_id=vehicle.tenant_id,
                            type="delay",
                            severity="medium",
                            title=f"Delay: {vehicle.registration_number}",
                            message=(
                                f"{vehicle.registration_number} is caught in traffic and "
                                "running behind schedule."
                            ),
                            vehicle_id=vehicle.id,
                            driver_id=vehicle.driver_id,
                            is_acknowledged=False,
                        )
                    )

        for tenant_id, total_drop in fuel_drops_by_tenant.items():
            if total_drop > 0:
                await upsert_daily_analytics(
                    db=db,
                    tenant_id=tenant_id,
                    record_date=timestamp.date(),
                    fuel_consumed=total_drop,
                )

        await db.commit()
