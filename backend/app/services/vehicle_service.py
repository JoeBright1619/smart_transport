from typing import Sequence

from fastapi import status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import _raise_error
from app.models.trip import Trip
from app.models.vehicle import Vehicle
from app.schemas.vehicle import VehicleCreate, VehicleUpdate
from app.services import audit_service, fleet_assignment, route_service, trip_service
from app.services.fleet_position import ensure_vehicle_position
from app.models.occupancy_event import OccupancyEvent


async def get_vehicles(
    db: AsyncSession,
    tenant_id: str,
    status_filter: str | None = None,
    route_id: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[Sequence[Vehicle], int]:
    query = select(Vehicle).where(
        Vehicle.tenant_id == tenant_id, Vehicle.is_deleted.is_(False)
    )

    if status_filter:
        query = query.where(Vehicle.status == status_filter)
    if route_id:
        query = query.where(Vehicle.route_id == route_id)

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    query = (
        query.offset((page - 1) * page_size)
        .limit(page_size)
        .order_by(Vehicle.created_at.desc())
    )
    result = await db.execute(query)
    vehicles = result.scalars().all()

    return vehicles, total


async def get_vehicle_by_id(
    db: AsyncSession, vehicle_id: str, tenant_id: str
) -> Vehicle:
    result = await db.execute(
        select(Vehicle).where(
            Vehicle.id == vehicle_id,
            Vehicle.tenant_id == tenant_id,
            Vehicle.is_deleted.is_(False),
        )
    )
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        _raise_error(
            status.HTTP_404_NOT_FOUND,
            "vehicle_not_found",
            "Vehicle not found",
        )
    return vehicle


async def get_latest_arrival_sequence(
    db: AsyncSession, vehicle_id: str, tenant_id: str
) -> int:
    """Return the highest occupancy-event arrival sequence for a vehicle.

    Raises:
        HTTPException(404, vehicle_not_found): unknown / cross-tenant vehicle.
        HTTPException(404, no_arrival_records): vehicle exists, zero events.
    """
    # Validates existence and tenant ownership; raises vehicle_not_found.
    await get_vehicle_by_id(db, vehicle_id, tenant_id)

    result = await db.execute(
        select(func.max(OccupancyEvent.arrival_sequence)).where(
            OccupancyEvent.vehicle_id == vehicle_id,
            OccupancyEvent.tenant_id == tenant_id,  # defense-in-depth
        )
    )
    latest = result.scalar_one_or_none()
    if latest is None:
        _raise_error(
            status.HTTP_404_NOT_FOUND,
            "no_arrival_records",
            "No arrival records for vehicle",
        )
    return latest


async def create_vehicle(
    db: AsyncSession, data: VehicleCreate, tenant_id: str, current_user_id: str
) -> Vehicle:
    # A brand-new vehicle has no trip, driver or route, so it cannot be "on a journey".
    # active is only reachable by starting a journey on an existing vehicle.
    if data.status == "active":
        _raise_error(
            status.HTTP_409_CONFLICT,
            "CANNOT_CREATE_ACTIVE",
            "A new vehicle cannot be created as active — add it, then start a journey",
        )

    existing = await db.execute(
        select(Vehicle).where(
            Vehicle.tenant_id == tenant_id,
            Vehicle.registration_number == data.registration_number,
            Vehicle.is_deleted.is_(False),
        )
    )
    if existing.scalar_one_or_none():
        _raise_error(
            status.HTTP_409_CONFLICT,
            "CONFLICT",
            "Vehicle with this registration number already exists",
        )

    vehicle = Vehicle(
        tenant_id=tenant_id,
        registration_number=data.registration_number,
        model=data.model,
        seating_capacity=data.seating_capacity,
        status=data.status,
    )
    # Every vehicle carries a last-known GPS position from creation (any status,
    # including offline) so the fleet is always locatable. Falls back to no GPS only
    # when the tenant has no stops to anchor to.
    await ensure_vehicle_position(db, vehicle)
    db.add(vehicle)
    await db.flush()
    await audit_service.log(
        db, current_user_id, tenant_id, "Vehicle", vehicle.id, "create"
    )
    return vehicle


async def guard_deactivation(
    db: AsyncSession, vehicle_id: str, new_status: str
) -> None:
    """Block idle/maintenance/offline transitions that would strand an open trip.

    Shared with maintenance_service so starting a maintenance job takes a vehicle off the
    road under exactly the same rules as a Fleet-screen maintenance change.
    """
    conflict_trip = (
        await db.execute(
            select(Trip).where(
                Trip.vehicle_id == vehicle_id,
                Trip.status.in_(["scheduled", "active"]),
                Trip.is_deleted.is_(False),
            )
        )
    ).scalar_one_or_none()
    if conflict_trip is None:
        return
    if conflict_trip.status == "active":
        _raise_error(
            status.HTTP_409_CONFLICT,
            "CONFLICT",
            "Vehicle has an active trip — complete or cancel the trip first",
        )
    if new_status in ("maintenance", "offline"):
        _raise_error(
            status.HTTP_409_CONFLICT,
            "CONFLICT",
            "Cannot set vehicle to maintenance or offline — it has a scheduled trip",
        )


async def _apply_status_change(
    db: AsyncSession,
    vehicle: Vehicle,
    new_status: str,
    tenant_id: str,
    current_user_id: str,
) -> None:
    """Apply a vehicle status change through the single journey lifecycle.

    ``active`` is never a free-set value — a running vehicle must be backed by a trip, so
    it routes through the guarded start-journey path (needs a driver + route already
    assigned). The journey's rounds count comes from dispatch (``create_trip``).
    Deactivations go through the open-trip guard.
    """
    if new_status == "active":
        await trip_service.start_journey(
            db, vehicle=vehicle, tenant_id=tenant_id, current_user_id=current_user_id
        )
        return
    if new_status in ("idle", "maintenance", "offline"):
        await guard_deactivation(db, vehicle.id, new_status)
    vehicle.status = new_status


async def update_vehicle(
    db: AsyncSession,
    vehicle_id: str,
    data: VehicleUpdate,
    tenant_id: str,
    current_user_id: str,
) -> Vehicle:
    vehicle = await get_vehicle_by_id(db, vehicle_id, tenant_id)

    update_data = data.model_dump(exclude_unset=True)
    # Handle assignments before status so a combined "assign + activate" request works.
    if "fuel" in update_data:
        vehicle.fuel = update_data["fuel"]
    if "seating_capacity" in update_data:
        vehicle.seating_capacity = update_data["seating_capacity"]
    if "route_id" in update_data:
        route_id = update_data["route_id"]
        if route_id is not None:
            await route_service.ensure_route_active(db, route_id, tenant_id)
        vehicle.route_id = route_id
    if "driver_id" in update_data:
        await fleet_assignment.set_vehicle_assignment(
            db, vehicle=vehicle, driver_id=update_data["driver_id"], tenant_id=tenant_id
        )

    if "status" in update_data:
        await _apply_status_change(
            db, vehicle, update_data["status"], tenant_id, current_user_id
        )
    # current_occupancy is owned by the simulation — silently ignored if passed

    await db.flush()
    await audit_service.log(
        db,
        current_user_id,
        tenant_id,
        "Vehicle",
        vehicle.id,
        "update",
        metadata=update_data,
    )
    return vehicle


async def delete_vehicle(
    db: AsyncSession, vehicle_id: str, tenant_id: str, current_user_id: str
) -> None:
    vehicle = await get_vehicle_by_id(db, vehicle_id, tenant_id)

    if vehicle.status == "active":
        _raise_error(
            status.HTTP_409_CONFLICT,
            "CONFLICT",
            "Cannot delete an active vehicle",
        )

    vehicle.is_deleted = True
    await db.flush()
    await audit_service.log(
        db, current_user_id, tenant_id, "Vehicle", vehicle.id, "soft_delete"
    )
