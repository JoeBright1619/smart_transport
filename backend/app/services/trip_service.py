from typing import Sequence
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trip import Trip
from app.models.driver import Driver
from app.models.vehicle import Vehicle
from app.schemas.trip import TripCreate, TripUpdate
from app.services import audit_service


def _error_detail(code: str, message: str) -> dict:
    return {
        "data": None,
        "meta": None,
        "error": {
            "code": code,
            "message": message,
        },
    }


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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_error_detail("NOT_FOUND", "Trip not found"),
        )
    return trip


async def create_trip(
    db: AsyncSession, data: TripCreate, tenant_id: str, current_user_id: str
) -> Trip:
    conflicting_trip = await db.execute(
        select(Trip).where(
            Trip.tenant_id == tenant_id,
            Trip.status.in_(["scheduled", "active"]),
            Trip.is_deleted.is_(False),
            or_(Trip.vehicle_id == data.vehicle_id, Trip.driver_id == data.driver_id),
        )
    )
    if conflicting_trip.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_error_detail(
                "CONFLICT", "Vehicle or driver already has an active or scheduled trip"
            ),
        )

    trip = Trip(
        tenant_id=tenant_id,
        vehicle_id=data.vehicle_id,
        route_id=data.route_id,
        driver_id=data.driver_id,
        scheduled_start=data.scheduled_start,
        scheduled_end=data.scheduled_end,
        status="scheduled",
    )
    db.add(trip)
    await db.flush()
    await audit_service.log(db, current_user_id, tenant_id, "Trip", trip.id, "create")
    return trip


VALID_TRANSITIONS = {
    "scheduled": ["active", "cancelled"],
    "active": ["completed", "cancelled"],
    "completed": [],
    "cancelled": [],
}


async def update_trip(
    db: AsyncSession,
    trip_id: str,
    data: TripUpdate,
    tenant_id: str,
    current_user_id: str,
) -> Trip:
    trip = await get_trip_by_id(db, trip_id, tenant_id)

    new_status = data.status
    if new_status not in VALID_TRANSITIONS.get(trip.status, []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_error_detail(
                "BAD_REQUEST",
                f"Invalid status transition from {trip.status} to {new_status}",
            ),
        )

    now = datetime.now(timezone.utc)

    trip.status = new_status
    if new_status == "active":
        trip.actual_start = now

        driver_result = await db.execute(
            select(Driver).where(Driver.id == trip.driver_id)
        )
        driver = driver_result.scalar_one_or_none()
        if driver:
            driver.status = "on-trip"

        vehicle_result = await db.execute(
            select(Vehicle).where(Vehicle.id == trip.vehicle_id)
        )
        vehicle = vehicle_result.scalar_one_or_none()
        if vehicle:
            vehicle.status = "active"

    elif new_status == "completed" or new_status == "cancelled":
        if new_status == "completed":
            trip.actual_end = now

        driver_result = await db.execute(
            select(Driver).where(Driver.id == trip.driver_id)
        )
        driver = driver_result.scalar_one_or_none()
        if driver and driver.status == "on-trip":
            driver.status = "available"
            if new_status == "completed":
                driver.total_trips += 1

        vehicle_result = await db.execute(
            select(Vehicle).where(Vehicle.id == trip.vehicle_id)
        )
        vehicle = vehicle_result.scalar_one_or_none()
        if vehicle and vehicle.status == "active":
            vehicle.status = "idle"

    await db.flush()
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
