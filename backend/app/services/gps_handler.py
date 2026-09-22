"""GPS position handler service for processing incoming GPS updates via MQTT.

This service is called by the MQTT subscriber when GPS position updates are received
from external GPS devices or the GPS service simulator.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.telemetry import Telemetry
from app.models.vehicle import Vehicle
from app.schemas.gps import GPSPositionUpdate
from app.services.alert_service import auto_generate

logger = logging.getLogger(__name__)

# Alert thresholds
LOW_FUEL_THRESHOLD = 15
SPEEDING_THRESHOLD = 65  # km/h


async def process_gps_update(
    db: AsyncSession,
    gps_data: GPSPositionUpdate,
) -> dict[str, str]:
    """Process a GPS position update and persist vehicle changes.

    Args:
        db: Database session
        gps_data: Validated GPS position update from MQTT

    Returns:
        dict with status and vehicle_id
    """
    # Look up the vehicle
    vehicle = await db.scalar(
        select(Vehicle).where(
            Vehicle.id == gps_data.vehicle_id,
            Vehicle.tenant_id == gps_data.tenant_id,
            Vehicle.is_deleted.is_(False),
        )
    )

    if vehicle is None:
        logger.warning(
            "GPS update for unknown vehicle: %s (tenant: %s)",
            gps_data.vehicle_id,
            gps_data.tenant_id,
        )
        return {"status": "vehicle_not_found", "vehicle_id": gps_data.vehicle_id}

    prev_fuel = vehicle.fuel or 100

    # Update vehicle position and status
    vehicle.lat = gps_data.lat
    vehicle.lng = gps_data.lng
    vehicle.speed = gps_data.speed
    vehicle.heading = gps_data.heading
    vehicle.fuel = gps_data.fuel
    vehicle.engine_status = gps_data.engine_status

    # Create telemetry record
    telemetry = Telemetry(
        tenant_id=gps_data.tenant_id,
        vehicle_id=gps_data.vehicle_id,
        lat=gps_data.lat,
        lng=gps_data.lng,
        speed=gps_data.speed,
        heading=gps_data.heading,
        timestamp=gps_data.timestamp or datetime.now(timezone.utc),
    )
    db.add(telemetry)

    # Trigger alerts using existing alert service
    await _trigger_alerts(db, vehicle, gps_data, prev_fuel)

    logger.debug(
        "Processed GPS update for vehicle %s: lat=%.4f, lng=%.4f, speed=%d",
        gps_data.vehicle_id,
        gps_data.lat,
        gps_data.lng,
        gps_data.speed,
    )

    return {"status": "processed", "vehicle_id": gps_data.vehicle_id}


async def _trigger_alerts(
    db: AsyncSession,
    vehicle: Vehicle,
    gps_data: GPSPositionUpdate,
    prev_fuel: int,
) -> None:
    """Trigger alerts based on GPS data using existing alert service."""
    # Low fuel alert (transition into low fuel zone)
    if gps_data.fuel < LOW_FUEL_THRESHOLD and prev_fuel >= LOW_FUEL_THRESHOLD:
        await auto_generate(db, gps_data.tenant_id, "maintenance", vehicle.id)
        logger.info(
            "Triggered low fuel alert for vehicle %s (fuel: %d%%)",
            vehicle.id,
            gps_data.fuel,
        )

    # Speeding alert
    if gps_data.speed > SPEEDING_THRESHOLD:
        await auto_generate(db, gps_data.tenant_id, "speeding", vehicle.id)
        logger.info(
            "Triggered speeding alert for vehicle %s (speed: %d km/h)",
            vehicle.id,
            gps_data.speed,
        )

    # Delay alert (checked by alert service based on trip status)
    await auto_generate(db, gps_data.tenant_id, "delay", vehicle.id)

    # Breakdown alert (based on engine status)
    if gps_data.engine_status == "critical":
        await auto_generate(db, gps_data.tenant_id, "breakdown", vehicle.id)
        logger.info(
            "Triggered breakdown alert for vehicle %s (engine: %s)",
            vehicle.id,
            gps_data.engine_status,
        )
