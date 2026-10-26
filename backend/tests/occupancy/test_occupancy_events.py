"""Tests for the occupancy event schema and models (design §5 and §8).

Split into three sections:

* **Schema** — pure ``OccupancyEvent`` validation. No DB, no fixtures.
  Authored against §5, not against the not-yet-updated wire model.
* **Models** — persistence and constraint behavior of ``occupancy_events``
  and ``boarding_passenger_events``, using the shared ``db`` fixture and
  entity factories from ``tests/conftest.py``.
* **FK behavior** — cascade / SET NULL semantics, exercised via core DELETE
  so the DB-level constraint fires (the shared ``test_engine`` enables
  ``PRAGMA foreign_keys=ON``).
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.boarding_passenger_event import (
    BoardingEventType,
    BoardingPassengerEvent,
)
from app.models.occupancy_event import OccupancyEvent
from app.models.user import User
from app.schemas.occupancy import OccupancyEvent as OccupancyEventSchema


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

# Representative payload per §5. Includes the fields the passenger_service
# Task 4.4 model does not yet emit (list fields + revenue_delta) — the backend
# schema is authored against §5, so this is what the wire should look like
# once Task 4.5 lands.
VALID_PAYLOAD = {
    "vehicle_id": "veh-001",
    "tenant_id": "ten-001",
    "stop_id": "stop-007",
    "route_id": "route-003",
    "onboard": 27,
    "boardings": 4,
    "alightings": 2,
    "arrival_sequence": 11,
    "position_timestamp": "2026-10-23T09:15:00+00:00",
    "service_timestamp": "2026-10-23T09:15:02+00:00",
    "idempotency_key": "veh-001:stop-007:11",
    "boarded_passenger_ids": ["user-a", "user-b", "user-c", "user-d"],
    "alighted_passenger_ids": ["user-x", "user-y"],
    "revenue_delta": 0.42,
}


def test_schema_parses_representative_payload() -> None:
    event = OccupancyEventSchema.model_validate(VALID_PAYLOAD)
    assert event.vehicle_id == "veh-001"
    assert event.onboard == 27
    assert event.revenue_delta == pytest.approx(0.42)


def test_schema_applies_defaults_for_optional_fields() -> None:
    # Minimal payload omitting every field that has a default.
    minimal = {
        k: VALID_PAYLOAD[k]
        for k in (
            "vehicle_id",
            "tenant_id",
            "stop_id",
            "route_id",
            "onboard",
            "boardings",
            "alightings",
            "arrival_sequence",
            "position_timestamp",
            "service_timestamp",
            "idempotency_key",
        )
    }
    event = OccupancyEventSchema.model_validate(minimal)
    assert event.source == "passenger_service"
    assert event.boarded_passenger_ids == []
    assert event.alighted_passenger_ids == []
    assert event.revenue_delta == 0.0


def test_schema_rejects_missing_required_field() -> None:
    payload = dict(VALID_PAYLOAD)
    payload.pop("vehicle_id")
    with pytest.raises(ValidationError):
        OccupancyEventSchema.model_validate(payload)


def test_schema_rejects_negative_revenue_delta() -> None:
    payload = {**VALID_PAYLOAD, "revenue_delta": -0.01}
    with pytest.raises(ValidationError):
        OccupancyEventSchema.model_validate(payload)


def test_schema_rejects_negative_counts() -> None:
    for field in ("onboard", "boardings", "alightings", "arrival_sequence"):
        payload = {**VALID_PAYLOAD, field: -1}
        with pytest.raises(ValidationError):
            OccupancyEventSchema.model_validate(payload)


def test_schema_extra_fields_ignored() -> None:
    payload = {**VALID_PAYLOAD, "unknown_future_field": "ignored"}
    event = OccupancyEventSchema.model_validate(payload)
    assert "unknown_future_field" not in event.model_dump()


# ---------------------------------------------------------------------------
# Model persistence
# ---------------------------------------------------------------------------


def _make_event(
    *,
    tenant_id: str,
    vehicle_id: str,
    key: str = "veh-001:stop-007:11",
) -> OccupancyEvent:
    return OccupancyEvent(
        tenant_id=tenant_id,
        vehicle_id=vehicle_id,
        stop_id="stop-007",
        route_id="route-003",
        arrival_sequence=11,
        boardings=4,
        alightings=2,
        onboard=27,
        idempotency_key=key,
        position_timestamp=datetime(2026, 10, 23, 9, 15, tzinfo=UTC),
        service_timestamp=datetime(2026, 10, 23, 9, 15, 2, tzinfo=UTC),
        revenue_delta=0.42,
    )


async def test_model_roundtrip(db: AsyncSession, tenant, vehicle) -> None:
    event = _make_event(tenant_id=tenant.id, vehicle_id=vehicle.id)
    db.add(event)
    await db.flush()

    fetched = (
        await db.execute(select(OccupancyEvent).where(OccupancyEvent.id == event.id))
    ).scalar_one()
    assert fetched.idempotency_key == "veh-001:stop-007:11"
    assert fetched.arrival_sequence == 11
    assert float(fetched.revenue_delta) == pytest.approx(0.42)


async def test_idempotency_key_is_unique(db: AsyncSession, tenant, vehicle) -> None:
    db.add(_make_event(tenant_id=tenant.id, vehicle_id=vehicle.id, key="dup-key"))
    await db.flush()

    db.add(_make_event(tenant_id=tenant.id, vehicle_id=vehicle.id, key="dup-key"))
    with pytest.raises(IntegrityError):
        await db.flush()
    await db.rollback()


# ---------------------------------------------------------------------------
# Foreign-key behavior
# ---------------------------------------------------------------------------


async def test_children_cascade_delete_with_parent(
    db: AsyncSession, tenant, vehicle
) -> None:
    parent = _make_event(tenant_id=tenant.id, vehicle_id=vehicle.id)
    db.add(parent)
    await db.flush()

    db.add_all(
        [
            BoardingPassengerEvent(
                occupancy_event_id=parent.id,
                passenger_id=None,
                event_type=BoardingEventType.boarded,
            ),
            BoardingPassengerEvent(
                occupancy_event_id=parent.id,
                passenger_id=None,
                event_type=BoardingEventType.alighted,
            ),
        ]
    )
    await db.flush()

    # Exercise the DB-level FK: DELETE the parent with SQL, not ORM cascade.
    await db.execute(delete(OccupancyEvent).where(OccupancyEvent.id == parent.id))
    await db.flush()

    remaining = (
        (
            await db.execute(
                select(BoardingPassengerEvent).where(
                    BoardingPassengerEvent.occupancy_event_id == parent.id
                )
            )
        )
        .scalars()
        .all()
    )
    assert remaining == []


async def test_passenger_id_set_null_on_user_delete(
    db: AsyncSession, tenant, vehicle, make_user
) -> None:
    user = await make_user(tenant_id=tenant.id, role="passenger")

    parent = _make_event(tenant_id=tenant.id, vehicle_id=vehicle.id)
    db.add(parent)
    await db.flush()

    child = BoardingPassengerEvent(
        occupancy_event_id=parent.id,
        passenger_id=user.id,
        event_type=BoardingEventType.boarded,
    )
    db.add(child)
    await db.flush()

    await db.execute(delete(User).where(User.id == user.id))
    await db.flush()

    await db.refresh(child)
    assert child.passenger_id is None
