from typing import Sequence
from datetime import datetime, timedelta, timezone

from fastapi import status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.errors import _raise_error
from app.models.route import Route, RouteStop, Stop
from app.models.trip import Trip
from app.models.driver import Driver
from app.models.vehicle import Vehicle
from app.schemas.trip import DEFAULT_JOURNEY_LOOPS, TripCreate, TripUpdate
from app.services import audit_service, route_service
from app.websocket import route_simulation


async def get_trips(
    db: AsyncSession,
    tenant_id: str,
    status_filter: str | None = None,
    vehicle_id: str | None = None,
    driver_id: str | None = None,
    route_id: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[Sequence[Trip], int]:
    query = select(Trip).where(Trip.tenant_id == tenant_id, Trip.is_deleted.is_(False))

    if status_filter:
        query = query.where(Trip.status == status_filter)
    if vehicle_id:
        query = query.where(Trip.vehicle_id == vehicle_id)
    if driver_id:
        query = query.where(Trip.driver_id == driver_id)
    if route_id:
        query = query.where(Trip.route_id == route_id)

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    query = (
        query.offset((page - 1) * page_size)
        .limit(page_size)
        .order_by(Trip.created_at.desc())
    )
    result = await db.execute(query)
    trips = result.scalars().all()

    return trips, total


async def get_trip_by_id(db: AsyncSession, trip_id: str, tenant_id: str) -> Trip:
    result = await db.execute(
        select(Trip).where(
            Trip.id == trip_id, Trip.tenant_id == tenant_id, Trip.is_deleted.is_(False)
        )
    )
    trip = result.scalar_one_or_none()
    if not trip:
        _raise_error(
            status.HTTP_404_NOT_FOUND,
            "NOT_FOUND",
            "Trip not found",
        )
    return trip


async def create_trip(
    db: AsyncSession, data: TripCreate, tenant_id: str, current_user_id: str
) -> Trip:
    # Validate vehicle belongs to tenant, is not deleted, and is dispatchable
    vehicle_result = await db.execute(
        select(Vehicle).where(
            Vehicle.id == data.vehicle_id,
            Vehicle.tenant_id == tenant_id,
            Vehicle.is_deleted.is_(False),
        )
    )
    vehicle = vehicle_result.scalar_one_or_none()
    if not vehicle:
        _raise_error(
            status.HTTP_404_NOT_FOUND,
            "vehicle_not_found",
            "Vehicle not found",
        )
    if vehicle.status in ("active", "maintenance", "offline"):
        _raise_error(
            status.HTTP_409_CONFLICT,
            "CONFLICT",
            f"Vehicle is not available for dispatch (status: {vehicle.status})",
        )

    # Validate driver belongs to tenant, is not deleted, and is dispatchable
    driver_result = await db.execute(
        select(Driver).where(
            Driver.id == data.driver_id,
            Driver.tenant_id == tenant_id,
            Driver.is_deleted.is_(False),
        )
    )
    driver = driver_result.scalar_one_or_none()
    if not driver:
        _raise_error(
            status.HTTP_404_NOT_FOUND,
            "NOT_FOUND",
            "Driver not found",
        )
    if driver.status == "on-trip":
        _raise_error(
            status.HTTP_409_CONFLICT,
            "CONFLICT",
            "Driver is currently on a trip",
        )

    # Route must exist and be active (not disabled) to dispatch onto it.
    await route_service.ensure_route_active(db, data.route_id, tenant_id)

    # Reject if vehicle or driver already has a scheduled/active trip
    conflicting_trip = await db.execute(
        select(Trip).where(
            Trip.tenant_id == tenant_id,
            Trip.status.in_(["scheduled", "active"]),
            Trip.is_deleted.is_(False),
            or_(Trip.vehicle_id == data.vehicle_id, Trip.driver_id == data.driver_id),
        )
    )
    if conflicting_trip.scalar_one_or_none():
        _raise_error(
            status.HTTP_409_CONFLICT,
            "CONFLICT",
            "Vehicle or driver already has an active or scheduled trip",
        )

    # The end is derived from the route and rounds unless the caller pins it explicitly:
    # scheduled_start + route.duration * planned_loops (the whole journey's expected end).
    scheduled_end = data.scheduled_end
    if scheduled_end is None:
        route_duration = await db.scalar(
            select(Route.duration).where(Route.id == data.route_id)
        )
        journey_minutes = (route_duration or 30) * data.planned_loops
        scheduled_end = data.scheduled_start + timedelta(minutes=journey_minutes)

    trip = Trip(
        tenant_id=tenant_id,
        vehicle_id=data.vehicle_id,
        route_id=data.route_id,
        driver_id=data.driver_id,
        scheduled_start=data.scheduled_start,
        scheduled_end=scheduled_end,
        status="scheduled",
    )
    db.add(trip)
    await db.flush()

    # Reserve the resources — link vehicle and driver to this trip
    vehicle.driver_id = trip.driver_id
    vehicle.route_id = trip.route_id
    driver.vehicle_id = trip.vehicle_id

    # The rounds count is chosen at dispatch: how many times the driver runs the route
    # before the journey auto-ends. It rides on the vehicle (the journey's home) and is
    # honoured by the simulation once the trip is activated.
    vehicle.planned_loops = data.planned_loops

    await audit_service.log(db, current_user_id, tenant_id, "Trip", trip.id, "create")
    return trip


VALID_TRANSITIONS = {
    "scheduled": ["active", "cancelled"],
    "active": ["completed", "cancelled"],
    "completed": [],
    "cancelled": [],
}


async def _activate_trip(db: AsyncSession, trip: Trip, now: datetime) -> None:
    """Put the trip's driver and vehicle on the road and start the rounds counter."""
    trip.actual_start = now

    # Departure delay = actual − scheduled start (signed minutes). A DB timestamp can be
    # tz-naive (e.g. SQLite) while ``now`` is tz-aware; normalise before subtracting.
    scheduled = trip.scheduled_start
    if scheduled.tzinfo is None:
        scheduled = scheduled.replace(tzinfo=timezone.utc)
    trip.start_delay = round((now - scheduled).total_seconds() / 60)

    driver = await db.scalar(select(Driver).where(Driver.id == trip.driver_id))
    if driver:
        driver.status = "on-trip"

    vehicle = await db.scalar(select(Vehicle).where(Vehicle.id == trip.vehicle_id))
    if not vehicle:
        return
    vehicle.status = "active"
    # Drop any leftover in-memory sim state so this journey initialises cleanly from the
    # vehicle's persisted values (fuel, position) rather than a previous journey's.
    route_simulation.clear_vehicle_state(vehicle.id)
    # Start the journey's rounds counter. planned_loops is only defaulted when the
    # caller (start_journey / dispatch) hasn't already chosen a count.
    vehicle.completed_loops = 0
    if vehicle.planned_loops is None:
        vehicle.planned_loops = DEFAULT_JOURNEY_LOOPS
    if vehicle.lat is None or vehicle.lng is None:
        first_stop = (
            await db.execute(
                select(Stop.lat, Stop.lng)
                .join(RouteStop, RouteStop.stop_id == Stop.id)
                .where(
                    RouteStop.route_id == trip.route_id,
                    Stop.is_deleted.is_(False),
                )
                .order_by(RouteStop.stop_order.asc())
                .limit(1)
            )
        ).first()
        if first_stop:
            vehicle.lat = first_stop.lat
            vehicle.lng = first_stop.lng


async def _finalize_trip(
    db: AsyncSession, trip: Trip, new_status: str, now: datetime
) -> None:
    """Complete or cancel a trip: free the driver and stand the vehicle down."""
    if new_status == "completed":
        trip.actual_end = now

    driver = await db.scalar(select(Driver).where(Driver.id == trip.driver_id))
    if driver:
        if driver.status == "on-trip":
            driver.status = "available"
            if new_status == "completed":
                driver.total_trips += 1
        driver.vehicle_id = None

    vehicle = await db.scalar(select(Vehicle).where(Vehicle.id == trip.vehicle_id))
    if vehicle:
        if vehicle.status == "active":
            vehicle.status = "idle"
        vehicle.driver_id = None
        vehicle.route_id = None
        # The journey is over — clear its rounds counter so a future journey starts
        # fresh rather than inheriting a stale/finished count.
        vehicle.planned_loops = None
        vehicle.completed_loops = 0
        # Back at the depot — refuel and drop any stale in-memory sim state so the next
        # journey starts clean (fresh fuel, position and loop counters).
        vehicle.fuel = 100
        route_simulation.clear_vehicle_state(vehicle.id)
        if new_status == "completed":
            vehicle.current_occupancy = 0


async def update_trip(
    db: AsyncSession,
    trip_id: str,
    data: TripUpdate,
    tenant_id: str,
    current_user_id: str | None,
) -> Trip:
    """Advance a trip through its lifecycle.

    ``current_user_id`` is ``None`` for automated (system) transitions — e.g. the
    auto-start dispatcher — in which case no audit row is written, since audit entries
    require a real user and there is no human actor.
    """
    trip = await get_trip_by_id(db, trip_id, tenant_id)

    new_status = data.status
    if new_status not in VALID_TRANSITIONS.get(trip.status, []):
        _raise_error(
            status.HTTP_400_BAD_REQUEST,
            "BAD_REQUEST",
            f"Invalid status transition from {trip.status} to {new_status}",
        )

    now = datetime.now(timezone.utc)

    trip.status = new_status
    if new_status == "active":
        await _activate_trip(db, trip, now)
    elif new_status in ("completed", "cancelled"):
        await _finalize_trip(db, trip, new_status, now)

    await db.flush()
    if current_user_id is not None:
        await audit_service.log(
            db,
            current_user_id,
            tenant_id,
            "Trip",
            trip.id,
            "update",
            metadata={"status": new_status},
        )
    return trip


async def start_journey(
    db: AsyncSession, *, vehicle: Vehicle, tenant_id: str, current_user_id: str
) -> Trip:
    """Start a journey now for a vehicle that already has a driver and route assigned.

    This is the single guarded operation for putting a vehicle on the road: it creates a
    trip (reusing ``create_trip``'s dispatchability/double-booking guards) and activates
    it, so the vehicle becomes ``active`` with GPS and the driver goes ``on-trip``. The
    Fleet screen ("set active") and any dispatch "start now" both funnel through here, so
    a running vehicle is *always* backed by exactly one active trip — the single source
    of truth for "on a journey". The rounds count comes from ``create_trip`` (the default,
    since the Fleet quick-start does not pick one).
    """
    if vehicle.driver_id is None or vehicle.route_id is None:
        _raise_error(
            status.HTTP_409_CONFLICT,
            "JOURNEY_REQUIRES_DRIVER_ROUTE",
            "Assign a driver and a route to the vehicle before starting a journey",
        )

    now = datetime.now(timezone.utc)
    trip = await create_trip(
        db,
        TripCreate(
            vehicle_id=vehicle.id,
            driver_id=vehicle.driver_id,
            route_id=vehicle.route_id,
            scheduled_start=now,
            # scheduled_end derived from the route + rounds by create_trip.
        ),
        tenant_id,
        current_user_id,
    )
    await update_trip(
        db, trip.id, TripUpdate(status="active"), tenant_id, current_user_id
    )
    return trip
