"""Tests for app.services.occupancy_service.record — Task 7.2."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select

from app.models.boarding_passenger_event import BoardingPassengerEvent
from app.models.occupancy_event import OccupancyEvent
from app.schemas.occupancy import OccupancyEvent as OccupancyEventSchema
from app.services import occupancy_service


def _event(
    *,
    vehicle_id: str,
    tenant_id: str,
    stop_id: str = "stop-x",
    route_id: str = "route-x",
    onboard: int = 10,
    boardings: int = 3,
    alightings: int = 1,
    arrival_sequence: int = 1,
    revenue_delta: float = 0.0,
    idempotency_key: str | None = None,
    boarded_passenger_ids: list[str] | None = None,
    alighted_passenger_ids: list[str] | None = None,
) -> OccupancyEventSchema:
    now = datetime.now(UTC).isoformat()
    return OccupancyEventSchema(
        vehicle_id=vehicle_id,
        tenant_id=tenant_id,
        stop_id=stop_id,
        route_id=route_id,
        onboard=onboard,
        boardings=boardings,
        alightings=alightings,
        arrival_sequence=arrival_sequence,
        position_timestamp=now,
        service_timestamp=now,
        idempotency_key=idempotency_key or f"{vehicle_id}:{stop_id}:{arrival_sequence}",
        boarded_passenger_ids=boarded_passenger_ids or [],
        alighted_passenger_ids=alighted_passenger_ids or [],
        revenue_delta=revenue_delta,
    )


async def test_record_inserts_event_and_updates_vehicle(db, tenant, vehicle) -> None:
    event = _event(vehicle_id=vehicle.id, tenant_id=tenant.id, onboard=12)

    await occupancy_service.record(db, event)
    await db.commit()

    # occupancy_events row exists
    row = (
        await db.execute(
            select(OccupancyEvent).where(
                OccupancyEvent.idempotency_key == event.idempotency_key
            )
        )
    ).scalar_one()
    assert row.onboard == 12

    # vehicle updated
    await db.refresh(vehicle)
    assert vehicle.current_occupancy == 12


async def test_record_writes_boarding_children(
    db, tenant, vehicle, passenger_user
) -> None:
    user_a = passenger_user
    user_b = passenger_user
    user_c = passenger_user
    event = _event(
        vehicle_id=vehicle.id,
        tenant_id=tenant.id,
        boarded_passenger_ids=[user_a.id, user_b.id],
        alighted_passenger_ids=[user_c.id],
    )

    await occupancy_service.record(db, event)
    await db.commit()

    parent = (
        await db.execute(
            select(OccupancyEvent).where(
                OccupancyEvent.idempotency_key == event.idempotency_key
            )
        )
    ).scalar_one()
    children = (
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

    # In test_record_writes_boarding_children:
    types = sorted(getattr(c.event_type, "value", c.event_type) for c in children)
    pids = sorted(c.passenger_id for c in children)
    assert types == ["alighted", "boarded", "boarded"]
    assert pids == sorted([user_a.id, user_b.id, user_c.id])


async def test_record_duplicate_skips_all_side_effects(
    db, tenant, vehicle, monkeypatch, passenger_user
) -> None:
    """Duplicate idempotency_key: no children, no vehicle update, no analytics, no alert."""
    analytics_mock = AsyncMock()
    alert_mock = AsyncMock(return_value=None)
    monkeypatch.setattr(
        "app.services.occupancy_service.analytics_service.upsert_daily_analytics",
        analytics_mock,
    )
    monkeypatch.setattr(
        "app.services.occupancy_service.alert_service.create_capacity_alert",
        alert_mock,
    )
    user_a = passenger_user
    event = _event(
        vehicle_id=vehicle.id,
        tenant_id=tenant.id,
        onboard=5,
        revenue_delta=100.0,
        boarded_passenger_ids=[user_a.id],
    )

    # First delivery — everything should fire.
    await occupancy_service.record(db, event)
    await db.commit()

    analytics_mock.reset_mock()
    alert_mock.reset_mock()

    # Second delivery — nothing should fire.
    await occupancy_service.record(db, event)
    await db.commit()

    analytics_mock.assert_not_awaited()
    alert_mock.assert_not_awaited()

    # Still exactly one parent row and one child row.
    parents = (
        (
            await db.execute(
                select(OccupancyEvent).where(
                    OccupancyEvent.idempotency_key == event.idempotency_key
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(parents) == 1
    children = (
        (
            await db.execute(
                select(BoardingPassengerEvent).where(
                    BoardingPassengerEvent.occupancy_event_id == parents[0].id
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(children) == 1


async def test_record_unknown_vehicle_skips(db, tenant, monkeypatch) -> None:
    alert_mock = AsyncMock(return_value=None)
    monkeypatch.setattr(
        "app.services.occupancy_service.alert_service.create_capacity_alert",
        alert_mock,
    )

    event = _event(vehicle_id="veh-does-not-exist", tenant_id=tenant.id, onboard=5)

    await occupancy_service.record(db, event)
    await db.commit()

    # No occupancy_events row was written.
    rows = (
        (
            await db.execute(
                select(OccupancyEvent).where(
                    OccupancyEvent.idempotency_key == event.idempotency_key
                )
            )
        )
        .scalars()
        .all()
    )
    assert rows == []
    alert_mock.assert_not_awaited()


async def test_record_analytics_called_when_revenue_positive(
    db, tenant, vehicle, monkeypatch
) -> None:
    analytics_mock = AsyncMock()
    monkeypatch.setattr(
        "app.services.occupancy_service.analytics_service.upsert_daily_analytics",
        analytics_mock,
    )

    event = _event(
        vehicle_id=vehicle.id,
        tenant_id=tenant.id,
        revenue_delta=250.0,
    )
    await occupancy_service.record(db, event)
    await db.commit()

    analytics_mock.assert_awaited_once()
    kwargs = analytics_mock.call_args.kwargs
    assert kwargs["tenant_id"] == tenant.id
    assert kwargs["revenue"] == 250.0


async def test_record_analytics_not_called_when_revenue_zero(
    db, tenant, vehicle, monkeypatch
) -> None:
    analytics_mock = AsyncMock()
    monkeypatch.setattr(
        "app.services.occupancy_service.analytics_service.upsert_daily_analytics",
        analytics_mock,
    )

    event = _event(vehicle_id=vehicle.id, tenant_id=tenant.id, revenue_delta=0.0)
    await occupancy_service.record(db, event)
    await db.commit()

    analytics_mock.assert_not_awaited()


async def test_record_alert_fires_at_threshold(
    db, tenant, vehicle, monkeypatch
) -> None:
    """onboard >= 0.9 * seating_capacity → create_capacity_alert is called."""
    alert_mock = AsyncMock(return_value=None)
    monkeypatch.setattr(
        "app.services.occupancy_service.alert_service.create_capacity_alert",
        alert_mock,
    )

    # seat capacity 45 → threshold 40
    vehicle.seating_capacity = 45
    await db.flush()

    event = _event(vehicle_id=vehicle.id, tenant_id=tenant.id, onboard=40)
    await occupancy_service.record(db, event)
    await db.commit()

    alert_mock.assert_awaited_once()
    kwargs = alert_mock.call_args.kwargs
    assert kwargs["threshold_fraction"] == 0.9
    assert kwargs["dedup_window_seconds"] == 300


async def test_record_alert_not_fired_below_threshold(
    db, tenant, vehicle, monkeypatch
) -> None:
    alert_mock = AsyncMock(return_value=None)
    monkeypatch.setattr(
        "app.services.occupancy_service.alert_service.create_capacity_alert",
        alert_mock,
    )

    vehicle.seating_capacity = 45
    await db.flush()

    # 39 < 0.9 * 45 = 40
    event = _event(vehicle_id=vehicle.id, tenant_id=tenant.id, onboard=39)
    await occupancy_service.record(db, event)
    await db.commit()

    alert_mock.assert_not_awaited()


async def test_record_malformed_timestamp_raises(db, tenant, vehicle) -> None:
    """Non-ISO timestamp strings fail before any side effect."""
    event = _event(vehicle_id=vehicle.id, tenant_id=tenant.id)
    # Tamper with the timestamp to a non-parseable value.
    event = event.model_copy(update={"service_timestamp": "not-a-timestamp"})

    with pytest.raises(ValueError):
        await occupancy_service.record(db, event)


async def test_record_boarding_children_cascade_with_parent(
    db, tenant, vehicle, passenger_user
) -> None:
    user_a = passenger_user
    user_b = passenger_user
    event = _event(
        vehicle_id=vehicle.id,
        tenant_id=tenant.id,
        boarded_passenger_ids=[user_a.id],
        alighted_passenger_ids=[user_b.id],
    )
    await occupancy_service.record(db, event)
    await db.commit()

    parent = (
        await db.execute(
            select(OccupancyEvent).where(
                OccupancyEvent.idempotency_key == event.idempotency_key
            )
        )
    ).scalar_one()
    child_count = (
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
    assert len(child_count) == 2

    await db.delete(parent)
    await db.commit()

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


async def test_record_revenue_accumulates_across_events(
    db, tenant, vehicle, monkeypatch
) -> None:
    """Two events with revenue → two upsert calls with correct amounts."""
    analytics_mock = AsyncMock()
    monkeypatch.setattr(
        "app.services.occupancy_service.analytics_service.upsert_daily_analytics",
        analytics_mock,
    )

    for i, amt in enumerate((100.0, 50.0), start=1):
        event = _event(
            vehicle_id=vehicle.id,
            tenant_id=tenant.id,
            arrival_sequence=i,
            revenue_delta=amt,
            idempotency_key=f"{vehicle.id}:stop-x:{i}",
        )
        await occupancy_service.record(db, event)
    await db.commit()

    assert analytics_mock.await_count == 2
    amounts = [c.kwargs["revenue"] for c in analytics_mock.call_args_list]
    assert amounts == [100.0, 50.0]


async def test_record_idempotency_key_collision_does_not_duplicate_children(
    db, tenant, vehicle, passenger_user
) -> None:
    """Two events with the same idempotency_key → one parent, one set of children."""
    user_a = passenger_user
    user_b = passenger_user

    event = _event(
        vehicle_id=vehicle.id,
        tenant_id=tenant.id,
        boarded_passenger_ids=[user_a.id, user_b.id],
    )
    await occupancy_service.record(db, event)
    await db.commit()
    await occupancy_service.record(db, event)
    await db.commit()

    parent = (
        (
            await db.execute(
                select(OccupancyEvent).where(
                    OccupancyEvent.idempotency_key == event.idempotency_key
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(parent) == 1

    children = (
        (
            await db.execute(
                select(BoardingPassengerEvent).where(
                    BoardingPassengerEvent.occupancy_event_id == parent[0].id
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(children) == 2  # not 4
