from typing import Sequence
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.driver import Driver
from app.models.trip import Trip
from app.schemas.driver import DriverCreate, DriverUpdate
from app.services import audit_service, fleet_assignment, trip_reconciliation


def _error_detail(code: str, message: str) -> dict:
    return {
        "data": None,
        "meta": None,
        "error": {
            "code": code,
            "message": message,
        },
    }


async def get_drivers(
    db: AsyncSession,
    tenant_id: str,
    status_filter: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[Sequence[Driver], int]:
    query = select(Driver).where(
        Driver.tenant_id == tenant_id, Driver.is_deleted.is_(False)
    )

    if status_filter:
        query = query.where(Driver.status == status_filter)

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    query = (
        query.offset((page - 1) * page_size)
        .limit(page_size)
        .order_by(Driver.created_at.desc())
    )
    result = await db.execute(query)
    drivers = result.scalars().all()

    return drivers, total


async def get_driver_by_id(db: AsyncSession, driver_id: str, tenant_id: str) -> Driver:
    result = await db.execute(
        select(Driver).where(
            Driver.id == driver_id,
            Driver.tenant_id == tenant_id,
            Driver.is_deleted.is_(False),
        )
    )
    driver = result.scalar_one_or_none()
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_error_detail("NOT_FOUND", "Driver not found"),
        )
    return driver


async def create_driver(
    db: AsyncSession, data: DriverCreate, tenant_id: str, current_user_id: str
) -> Driver:
    existing = await db.execute(
        select(Driver).where(
            Driver.license_number == data.license_number, Driver.is_deleted.is_(False)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_error_detail(
                "CONFLICT", "Driver with this license number already exists"
            ),
        )

    expiry_dt = datetime.combine(
        data.certification_expiry, datetime.min.time(), tzinfo=timezone.utc
    )

    driver = Driver(
        tenant_id=tenant_id,
        name=data.name,
        license_number=data.license_number,
        phone=data.phone,
        certification_expiry=expiry_dt,
        status="available",
        rating=0.0,
        total_trips=0,
    )
    db.add(driver)
    await db.flush()
    await audit_service.log(
        db, current_user_id, tenant_id, "Driver", driver.id, "create"
    )
    return driver


async def update_driver(
    db: AsyncSession,
    driver_id: str,
    data: DriverUpdate,
    tenant_id: str,
    current_user_id: str,
) -> Driver:
    driver = await get_driver_by_id(db, driver_id, tenant_id)

    update_data = data.model_dump(exclude_unset=True)

    if "status" in update_data:
        new_status = update_data["status"]
        if new_status == "on-trip" and driver.status != "on-trip":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=_error_detail(
                    "BAD_REQUEST", "Cannot manually set status to on-trip"
                ),
            )
        if new_status == "off-duty":
            # Self-heal first: clear any orphaned trips (from a restarted/deactivated
            # simulation) so a stale 'active' row doesn't block off-duty forever.
            await trip_reconciliation.reconcile_orphaned_trips(
                db, tenant_id=tenant_id, driver_id=driver_id
            )
            conflict_result = await db.execute(
                select(Trip).where(
                    Trip.driver_id == driver_id,
                    Trip.status.in_(["scheduled", "active"]),
                    Trip.is_deleted.is_(False),
                )
            )
            if conflict_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=_error_detail(
                        "CONFLICT",
                        "Cannot set driver to off-duty — they have an active or scheduled trip",
                    ),
                )
        driver.status = new_status

    if "name" in update_data:
        driver.name = update_data["name"]
    if "phone" in update_data:
        driver.phone = update_data["phone"]
    if "vehicle_id" in update_data:
        await fleet_assignment.set_driver_assignment(
            db, driver=driver, vehicle_id=update_data["vehicle_id"], tenant_id=tenant_id
        )
    if "certification_expiry" in update_data:
        driver.certification_expiry = datetime.combine(
            update_data["certification_expiry"],
            datetime.min.time(),
            tzinfo=timezone.utc,
        )

    # We remove certification_expiry from metadata since it is a date and might cause JSON serialization issues,
    # instead we let string dump handle it
    dumped_metadata = data.model_dump(exclude_unset=True, mode="json")

    await db.flush()
    await audit_service.log(
        db,
        current_user_id,
        tenant_id,
        "Driver",
        driver.id,
        "update",
        metadata=dumped_metadata,
    )
    return driver


async def delete_driver(
    db: AsyncSession, driver_id: str, tenant_id: str, current_user_id: str
) -> None:
    driver = await get_driver_by_id(db, driver_id, tenant_id)

    if driver.status == "on-trip":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_error_detail(
                "BAD_REQUEST", "Cannot delete a driver who is currently on-trip"
            ),
        )

    driver.is_deleted = True
    await db.flush()
    await audit_service.log(
        db, current_user_id, tenant_id, "Driver", driver.id, "soft_delete"
    )
