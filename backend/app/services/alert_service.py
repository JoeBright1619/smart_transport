from typing import Sequence

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.vehicle import Vehicle
from app.models.trip import Trip


async def get_alerts(
    db: AsyncSession,
    tenant_id: str,
    severity: str | None = None,
    type_filter: str | None = None,
    is_acknowledged: bool | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[Sequence[Alert], int]:
    query = select(Alert).where(Alert.tenant_id == tenant_id)

    if severity:
        query = query.where(Alert.severity == severity)
    if type_filter:
        query = query.where(Alert.type == type_filter)
    if is_acknowledged is not None:
        query = query.where(Alert.is_acknowledged == is_acknowledged)

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    query = (
        query.offset((page - 1) * page_size)
        .limit(page_size)
        .order_by(Alert.created_at.desc())
    )
    result = await db.execute(query)
    alerts = result.scalars().all()

    return alerts, total


async def acknowledge_alert(db: AsyncSession, alert_id: str, tenant_id: str) -> Alert:
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id, Alert.tenant_id == tenant_id)
    )
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "data": None,
                "meta": None,
                "error": {"code": "NOT_FOUND", "message": "Alert not found"},
            },
        )

    alert.is_acknowledged = True
    await db.flush()
    return alert


async def auto_generate(
    db: AsyncSession, tenant_id: str, trigger_type: str, vehicle_id: str | None = None
) -> Alert | None:
    # 1. Duplicate suppression
    if vehicle_id:
        existing = await db.execute(
            select(Alert).where(
                Alert.tenant_id == tenant_id,
                Alert.type == trigger_type,
                Alert.vehicle_id == vehicle_id,
                Alert.is_acknowledged.is_(False),
            )
        )
        if existing.scalars().first():
            return None  # Suppressed because unacknowledged alert of same type + vehicle exists

    # 2. Check conditions and generate payload
    title = ""
    message = ""
    severity = "medium"
    driver_id = None

    if trigger_type == "delay":
        if not vehicle_id:
            return None
        trip_res = await db.execute(
            select(Trip).where(
                Trip.vehicle_id == vehicle_id,
                Trip.status == "active",
                Trip.tenant_id == tenant_id,
            )
        )
        trip = trip_res.scalars().first()
        if not trip or trip.delay <= 5:
            return None
        title = "Trip Delay"
        message = f"Vehicle is {trip.delay} minutes behind schedule."
        severity = "medium"
        driver_id = trip.driver_id

    elif trigger_type == "breakdown":
        if not vehicle_id:
            return None
        veh_res = await db.execute(
            select(Vehicle).where(
                Vehicle.id == vehicle_id, Vehicle.tenant_id == tenant_id
            )
        )
        veh = veh_res.scalars().first()
        if not veh or veh.engine_status != "critical":
            return None
        title = "Vehicle Breakdown"
        message = f"Engine status is critical for vehicle {veh.registration_number}."
        severity = "critical"
        driver_id = veh.driver_id

    elif trigger_type == "speeding":
        if not vehicle_id:
            return None
        veh_res = await db.execute(
            select(Vehicle).where(
                Vehicle.id == vehicle_id, Vehicle.tenant_id == tenant_id
            )
        )
        veh = veh_res.scalars().first()
        if not veh or (veh.speed or 0) <= 80:
            return None
        title = "Speeding Alert"
        message = f"Vehicle {veh.registration_number} exceeded 80 km/h (Current: {veh.speed} km/h)."
        severity = "high"
        driver_id = veh.driver_id

    elif trigger_type == "geofence":
        if not vehicle_id:
            return None
        title = "Geofence Breach"
        message = "Vehicle exited assigned route corridor."
        severity = "medium"

    elif trigger_type == "info":
        title = "Information"
        message = "General info alert."
        severity = "low"

    elif trigger_type == "maintenance":
        title = "Maintenance Due"
        message = "Vehicle requires upcoming maintenance within 7 days."
        severity = "high"
    else:
        return None

    # 3. Create Alert
    alert = Alert(
        tenant_id=tenant_id,
        type=trigger_type,
        severity=severity,
        title=title,
        message=message,
        vehicle_id=vehicle_id,
        driver_id=driver_id,
        is_acknowledged=False,
    )
    db.add(alert)
    await db.flush()
    return alert


async def create_capacity_alert(
    db: AsyncSession,
    vehicle: Vehicle,
    current_occupancy: int,
    stop_name: str,
) -> Alert | None:
    """Create a capacity alert when a bus reaches or exceeds seating capacity.

    Suppressed if an unacknowledged capacity alert already exists for this vehicle.
    """
    from app.websocket.manager import (
        manager,
    )  # lazy: avoid circular import at module load

    if current_occupancy < vehicle.seating_capacity:
        return None

    existing = await db.execute(
        select(Alert).where(
            Alert.tenant_id == vehicle.tenant_id,
            Alert.type == "capacity",
            Alert.vehicle_id == vehicle.id,
            Alert.is_acknowledged.is_(False),
        )
    )
    if existing.scalars().first():
        return None

    if current_occupancy > vehicle.seating_capacity:
        severity = "critical"
        title = f"Excess Passengers: {vehicle.registration_number}"
        message = (
            f"{vehicle.registration_number} carrying {current_occupancy} passengers "
            f"({vehicle.seating_capacity} seats) at stop: {stop_name}."
        )
    else:
        severity = "high"
        title = f"Bus Full: {vehicle.registration_number}"
        message = (
            f"{vehicle.registration_number} is at full capacity ({vehicle.seating_capacity} seats) "
            f"at stop: {stop_name}."
        )

    alert = Alert(
        tenant_id=vehicle.tenant_id,
        type="capacity",
        severity=severity,
        title=title,
        message=message,
        vehicle_id=vehicle.id,
        is_acknowledged=False,
    )
    db.add(alert)
    await db.flush()

    await manager.publish_to_tenant(
        vehicle.tenant_id,
        {
            "type": "new_alert",
            "alert": {
                "id": alert.id,
                "type": alert.type,
                "severity": alert.severity,
                "title": alert.title,
                "message": alert.message,
                "vehicleId": alert.vehicle_id,
                "isAcknowledged": alert.is_acknowledged,
            },
        },
    )
    return alert
