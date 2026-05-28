from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from contextlib import suppress
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.crud.analytics import upsert_daily_analytics
from app.models.alert import Alert
from app.models.telemetry import Telemetry
from app.models.vehicle import Vehicle
from app.websocket.route_simulation import (
    LOW_FUEL_THRESHOLD,
    TICK_SECONDS,
    advance_vehicle,
)

logger = logging.getLogger(__name__)
_simulation_task: asyncio.Task[None] | None = None


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
            await simulate_active_vehicles()
        except Exception:
            logger.warning("Vehicle simulation cycle failed", exc_info=True)

        await asyncio.sleep(TICK_SECONDS)


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

        for tenant_id, total_drop in fuel_drops_by_tenant.items():
            if total_drop > 0:
                await upsert_daily_analytics(
                    db=db,
                    tenant_id=tenant_id,
                    record_date=timestamp.date(),
                    fuel_consumed=total_drop,
                )

        await db.commit()
