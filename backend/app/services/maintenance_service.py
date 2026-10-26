from datetime import datetime, timezone
from typing import Sequence

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.maintenance import MaintenanceRecord
from app.models.vehicle import Vehicle
from app.schemas.maintenance import MaintenanceCreate, MaintenanceUpdate
from app.services import audit_service, vehicle_service


def _error_detail(code: str, message: str) -> dict:
    return {
        "data": None,
        "meta": None,
        "error": {
            "code": code,
            "message": message,
        },
    }


async def get_maintenance_records(
    db: AsyncSession,
    tenant_id: str,
    vehicle_id: str | None = None,
    status_filter: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[Sequence[MaintenanceRecord], int]:
    query = select(MaintenanceRecord).where(
        MaintenanceRecord.tenant_id == tenant_id,
        MaintenanceRecord.is_deleted.is_(False),
    )

    if vehicle_id:
        query = query.where(MaintenanceRecord.vehicle_id == vehicle_id)
    if status_filter:
        query = query.where(MaintenanceRecord.status == status_filter)

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    query = (
        query.offset((page - 1) * page_size)
        .limit(page_size)
        .order_by(MaintenanceRecord.scheduled_date.asc())
    )
    result = await db.execute(query)
    records = result.scalars().all()

    return records, total


async def get_maintenance_record_by_id(
    db: AsyncSession, record_id: str, tenant_id: str
) -> MaintenanceRecord:
    result = await db.execute(
        select(MaintenanceRecord).where(
            MaintenanceRecord.id == record_id,
            MaintenanceRecord.tenant_id == tenant_id,
            MaintenanceRecord.is_deleted.is_(False),
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_error_detail("NOT_FOUND", "Maintenance record not found"),
        )
    return record


async def create_maintenance_record(
    db: AsyncSession, data: MaintenanceCreate, tenant_id: str, current_user_id: str
) -> MaintenanceRecord:
    vehicle_res = await db.execute(
        select(Vehicle).where(
            Vehicle.id == data.vehicle_id, Vehicle.tenant_id == tenant_id
        )
    )
    if not vehicle_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_error_detail("vehicle_not_found", "Vehicle not found"),
        )

    record = MaintenanceRecord(
        tenant_id=tenant_id,
        vehicle_id=data.vehicle_id,
        type=data.type,
        description=data.description,
        scheduled_date=data.scheduled_date,
        cost=data.cost,
        next_due=data.next_due,
        status="scheduled",
    )
    db.add(record)
    await db.flush()
    await audit_service.log(
        db, current_user_id, tenant_id, "MaintenanceRecord", record.id, "create"
    )
    return record


async def _sync_vehicle_status(
    db: AsyncSession, record: MaintenanceRecord, new_status: str
) -> None:
    """Keep the vehicle's status in step with its maintenance record.

    Starting a job (``in-progress``) takes the vehicle off the road, guarded exactly like a
    Fleet-screen maintenance change (can't strand an active/scheduled trip). Leaving
    ``in-progress`` (completed or back to scheduled) returns the vehicle to ``idle`` — but
    only once no other job on it is still open.
    """
    vehicle = await db.get(Vehicle, record.vehicle_id)
    if vehicle is None:
        return

    if new_status == "in-progress":
        await vehicle_service.guard_deactivation(db, vehicle.id, "maintenance")
        vehicle.status = "maintenance"
        return

    if vehicle.status != "maintenance":
        return
    other_open = await db.scalar(
        select(MaintenanceRecord.id).where(
            MaintenanceRecord.vehicle_id == vehicle.id,
            MaintenanceRecord.id != record.id,
            MaintenanceRecord.status == "in-progress",
            MaintenanceRecord.is_deleted.is_(False),
        )
    )
    if other_open is None:
        vehicle.status = "idle"


async def update_maintenance_record(
    db: AsyncSession,
    record_id: str,
    data: MaintenanceUpdate,
    tenant_id: str,
    current_user_id: str,
) -> MaintenanceRecord:
    record = await get_maintenance_record_by_id(db, record_id, tenant_id)

    update_data = data.model_dump(exclude_unset=True)

    if "cost" in update_data:
        record.cost = update_data["cost"]

    if "status" in update_data:
        # Sync the vehicle first: the guard may reject starting maintenance, and that must
        # happen before the record's own status is mutated.
        await _sync_vehicle_status(db, record, update_data["status"])
        record.status = update_data["status"]

    if "completed_date" in update_data:
        record.completed_date = update_data["completed_date"]

    # Auto-fill completed_date if status is completed and completed_date is not set
    if record.status == "completed" and not record.completed_date:
        record.completed_date = datetime.now(timezone.utc).date()

    dump_meta = data.model_dump(exclude_unset=True, mode="json")

    await db.flush()
    await audit_service.log(
        db,
        current_user_id,
        tenant_id,
        "MaintenanceRecord",
        record.id,
        "update",
        metadata=dump_meta,
    )
    return record
