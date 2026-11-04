"""Occupancy event ingestion service (design §8).

Consumes validated OccupancyEvent payloads (from the MQTT subscriber,
Task 7.1) and writes them to the backend in a single transaction:

1. occupancy_events insert (ON CONFLICT idempotency_key DO NOTHING)
2. if inserted: boarding_passenger_events bulk insert,
   vehicles.current_occupancy update, analytics_daily revenue upsert,
   and — when over threshold — a capacity alert
3. the caller commits

Duplicate deliveries (same idempotency_key) skip every side effect in
step 2, including the alert. This is the mechanism §4 relies on to keep
replays safe.

Session ownership: the caller passes the AsyncSession and commits after
this returns. `record` never commits — it flushes and relies on the
caller's transaction, mirroring gps_handler.process_gps_update.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func, insert, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.boarding_passenger_event import BoardingPassengerEvent
from app.models.occupancy_event import OccupancyEvent
from app.models.route import Stop
from app.models.vehicle import Vehicle
from app.schemas.occupancy import OccupancyEvent as OccupancyEventSchema
from app.services import alert_service, vehicle_service
from app.crud import analytics as analytics_service

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RecordResult:
    """Outcome of record(db, event).

    inserted is False when the event was a duplicate (same idempotency_key)
    or when the vehicle was unknown. seating_capacity is populated only on
    insert (needed for the occupancy WebSocket broadcast, Task 7.3).
    """

    inserted: bool
    seating_capacity: int | None


async def record(db: AsyncSession, event: OccupancyEventSchema) -> RecordResult:
    """Idempotently persist an occupancy event and its side effects.

    Unknown vehicle: log WARNING and return (no side effects).
    Duplicate idempotency_key: log INFO and return (no side effects).
    Any other failure (DB, constraint): propagates. The subscriber
    (Task 7.1) catches and drops.
    """

    # 1. Vehicle lookup (tenant-scoped). Unknown → skip.
    try:
        vehicle = await vehicle_service.get_vehicle_by_id(
            db, event.vehicle_id, event.tenant_id
        )
    except HTTPException:
        logger.warning(
            "Occupancy event for unknown vehicle %s (tenant %s); skipping",
            event.vehicle_id,
            event.tenant_id,
        )
        return RecordResult(inserted=False, seating_capacity=None)

    # 2. Idempotent insert; bail out on duplicate before any side effect.
    inserted_id = await _insert_occupancy_or_none(db, event)
    if inserted_id is None:
        logger.info(
            "Duplicate occupancy event (idempotency_key=%s); skipping side effects",
            event.idempotency_key,
        )
        return RecordResult(inserted=False, seating_capacity=None)

    # 3. Side effects — one transaction, caller commits.
    await _insert_boarding_children(db, inserted_id, event)
    await _update_vehicle_occupancy(db, event.vehicle_id, event.onboard)

    service_ts = _parse_ts(event.service_timestamp)

    if event.revenue_delta > 0:
        await analytics_service.upsert_daily_analytics(
            db,
            tenant_id=event.tenant_id,
            record_date=service_ts.date(),
            revenue=event.revenue_delta,
        )

    threshold_count = int(vehicle.seating_capacity * settings.CAPACITY_ALERT_THRESHOLD)
    if event.onboard >= threshold_count:
        stop_name = await _resolve_stop_name(db, event.stop_id, event.tenant_id)
        await alert_service.create_capacity_alert(
            db,
            vehicle,
            current_occupancy=event.onboard,
            stop_name=stop_name,
            threshold_fraction=settings.CAPACITY_ALERT_THRESHOLD,
            dedup_window_seconds=settings.CAPACITY_ALERT_DEDUP_SECONDS,
        )
    return RecordResult(inserted=True, seating_capacity=vehicle.seating_capacity)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _insert_occupancy_or_none(
    db: AsyncSession, event: OccupancyEventSchema
) -> str | None:
    """Insert the occupancy event; return its id on insert, None on duplicate.

    Uses dialect-specific ON CONFLICT DO NOTHING ... RETURNING. Postgres
    is the production target; SQLite is the test target. Both dialects
    support this pair (SQLite ≥ 3.35 for RETURNING).
    """

    dialect = db.bind.dialect.name if db.bind is not None else "postgresql"
    insert_fn = sqlite_insert if dialect == "sqlite" else pg_insert

    stmt = (
        insert_fn(OccupancyEvent)
        .values(
            tenant_id=event.tenant_id,
            vehicle_id=event.vehicle_id,
            stop_id=event.stop_id,
            route_id=event.route_id,
            arrival_sequence=event.arrival_sequence,
            boardings=event.boardings,
            alightings=event.alightings,
            onboard=event.onboard,
            idempotency_key=event.idempotency_key,
            position_timestamp=_parse_ts(event.position_timestamp),
            service_timestamp=_parse_ts(event.service_timestamp),
            revenue_delta=event.revenue_delta,
        )
        .on_conflict_do_nothing(index_elements=["idempotency_key"])
        .returning(OccupancyEvent.id)
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def _insert_boarding_children(
    db: AsyncSession, occupancy_event_id: str, event: OccupancyEventSchema
) -> None:
    """Bulk-insert boarded and alighted passenger rows for a parent event."""

    rows: list[dict] = [
        {
            "occupancy_event_id": occupancy_event_id,
            "passenger_id": pid,
            "event_type": "boarded",
        }
        for pid in event.boarded_passenger_ids
    ] + [
        {
            "occupancy_event_id": occupancy_event_id,
            "passenger_id": pid,
            "event_type": "alighted",
        }
        for pid in event.alighted_passenger_ids
    ]

    if rows:
        await db.execute(insert(BoardingPassengerEvent).values(rows))


async def _update_vehicle_occupancy(
    db: AsyncSession, vehicle_id: str, onboard: int
) -> None:
    await db.execute(
        update(Vehicle)
        .where(Vehicle.id == vehicle_id)
        .values(current_occupancy=onboard, updated_at=func.now())
    )


async def _resolve_stop_name(db: AsyncSession, stop_id: str, tenant_id: str) -> str:
    """Return the stop's name, or the stop_id if the stop is unknown/deleted.

    The alert message is nicer with the name; the stop_id is a safe
    fallback (the alert is still actionable).
    """

    result = await db.execute(
        select(Stop.name).where(
            Stop.id == stop_id,
            Stop.tenant_id == tenant_id,
            Stop.is_deleted.is_(False),
        )
    )
    name = result.scalar_one_or_none()
    return name if name is not None else stop_id


def _parse_ts(value: str | datetime) -> datetime:
    """Parse a wire timestamp string (ISO 8601) or pass through a datetime."""
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value)
