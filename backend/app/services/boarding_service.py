"""Boarding record persistence and queries."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.boarding_record import BoardingRecord
from app.models.route import Stop
from app.models.trip import Trip
from app.models.vehicle import Vehicle
from app.schemas.boarding import BoardingRecordRead, PassengerTripRead


async def list_boardings(
    db: AsyncSession,
    tenant_id: str,
    trip_id: str | None,
    stop_id: str | None,
    date_from: date | None,
    date_to: date | None,
    page: int,
    page_size: int,
) -> tuple[list[BoardingRecordRead], int]:
    from sqlalchemy import func

    filters = [BoardingRecord.tenant_id == tenant_id]
    if trip_id:
        filters.append(BoardingRecord.trip_id == trip_id)
    if stop_id:
        filters.append(BoardingRecord.stop_id == stop_id)
    if date_from:
        filters.append(
            BoardingRecord.recorded_at
            >= datetime(
                date_from.year, date_from.month, date_from.day, tzinfo=timezone.utc
            )
        )
    if date_to:
        filters.append(
            BoardingRecord.recorded_at
            < datetime(
                date_to.year, date_to.month, date_to.day + 1, tzinfo=timezone.utc
            )
        )

    total = (
        await db.scalar(
            select(func.count()).select_from(BoardingRecord).where(and_(*filters))
        )
        or 0
    )

    rows = (
        await db.execute(
            select(BoardingRecord, Stop.name.label("stop_name"))
            .outerjoin(Stop, Stop.id == BoardingRecord.stop_id)
            .where(and_(*filters))
            .order_by(BoardingRecord.recorded_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()

    result = [
        BoardingRecordRead(
            id=r.BoardingRecord.id,
            trip_id=r.BoardingRecord.trip_id,
            stop_id=r.BoardingRecord.stop_id,
            stop_name=r.stop_name or "",
            passenger_id=r.BoardingRecord.passenger_id,
            event_type=r.BoardingRecord.event_type,
            count=r.BoardingRecord.count,
            recorded_at=r.BoardingRecord.recorded_at,
            occupancy_after=r.BoardingRecord.occupancy_after,
            tenant_id=r.BoardingRecord.tenant_id,
        )
        for r in rows
    ]
    return result, total


async def list_my_boardings(
    db: AsyncSession,
    passenger_id: str,
    page: int,
    page_size: int,
) -> tuple[list[PassengerTripRead], int]:
    from sqlalchemy import func

    filters = [BoardingRecord.passenger_id == passenger_id]
    total = (
        await db.scalar(
            select(func.count()).select_from(BoardingRecord).where(*filters)
        )
        or 0
    )

    rows = (
        await db.execute(
            select(
                BoardingRecord,
                Stop.name.label("stop_name"),
                Vehicle.registration_number.label("vehicle_registration"),
                Vehicle.model.label("vehicle_model"),
            )
            .outerjoin(Stop, Stop.id == BoardingRecord.stop_id)
            .outerjoin(Trip, Trip.id == BoardingRecord.trip_id)
            .outerjoin(Vehicle, Vehicle.id == Trip.vehicle_id)
            .where(*filters)
            .order_by(BoardingRecord.recorded_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()

    result = [
        PassengerTripRead(
            boarding_id=r.BoardingRecord.id,
            event_type=r.BoardingRecord.event_type,
            count=r.BoardingRecord.count,
            stop_id=r.BoardingRecord.stop_id,
            stop_name=r.stop_name or "",
            trip_id=r.BoardingRecord.trip_id,
            recorded_at=r.BoardingRecord.recorded_at,
            occupancy_after=r.BoardingRecord.occupancy_after,
            vehicle_registration=r.vehicle_registration,
            vehicle_model=r.vehicle_model,
        )
        for r in rows
    ]
    return result, total
