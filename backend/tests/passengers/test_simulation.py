"""Tests for passenger-linked boarding simulation (Task 4.1)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.boarding_record import BoardingRecord
from app.services.boarding_service import record_single_boarding
from app.websocket.passenger_simulation import simulate_passengers_at_stop


@pytest.fixture
async def sim_stop(make_stop, tenant):
    return await make_stop(
        tenant_id=tenant.id, name="Simulation Test Stop", lat=0.0, lng=0.0
    )


@pytest.fixture
async def sim_stops(tenant, db: AsyncSession):
    """Three collinear stops for route-simulation tests."""
    from app.models.route import Stop

    stops = [
        Stop(
            id=f"stop-route-{i}",
            tenant_id=tenant.id,
            name=f"Stop {i}",
            lat=float(i),
            lng=0.0,
            is_deleted=False,
        )
        for i in range(3)
    ]
    for s in stops:
        db.add(s)
    await db.commit()
    return stops


@pytest.mark.asyncio
async def test_record_single_boarding_creates_linked_pair(
    db: AsyncSession, tenant, sim_stop
):
    """Board then alight a passenger through the helper; exactly 2 linked rows exist."""
    passenger_id = "user-sim-passenger-01"
    now = datetime.now(timezone.utc)

    await record_single_boarding(
        db,
        trip_id=None,
        stop_id=sim_stop.id,
        passenger_id=passenger_id,
        event_type="boarded",
        tenant_id=tenant.id,
        occupancy_after=5,
        now=now,
    )
    await record_single_boarding(
        db,
        trip_id=None,
        stop_id=sim_stop.id,
        passenger_id=passenger_id,
        event_type="alighted",
        tenant_id=tenant.id,
        occupancy_after=4,
        now=now,
    )
    await db.flush()

    rows = (
        await db.scalars(
            select(BoardingRecord).where(BoardingRecord.passenger_id == passenger_id)
        )
    ).all()

    assert len(rows) == 2
    event_types = {r.event_type for r in rows}
    assert "boarded" in event_types
    assert "alighted" in event_types
    assert all(r.passenger_id == passenger_id for r in rows)


@pytest.mark.asyncio
async def test_through_passengers_stripped_of_id_at_last_stop(
    db: AsyncSession, tenant, make_vehicle, sim_stops
):
    """Tracked through-passengers at the last stop get an alighted record and
    carry forward with passenger_id=None so the board→alight pair is complete."""
    vehicle = await make_vehicle(tenant_id=tenant.id, status="active", lat=0.0, lng=0.0)
    vehicle.seating_capacity = 20
    vehicle.current_occupancy = 8

    tracked_id = "user-through-tracked-01"
    # Pre-load state: 8 passengers, first two have tracked IDs; all have
    # dest_index = last stop so they'd alight — through-passenger logic may
    # keep some anyway.
    last_idx = len(sim_stops) - 1
    state: dict = {
        "passengers": [
            {
                "origin_index": 0,
                "dest_index": last_idx,
                "distance_km": 1.0,
                "passenger_id": tracked_id,
            },
            {
                "origin_index": 0,
                "dest_index": last_idx,
                "distance_km": 1.0,
                "passenger_id": "user-through-tracked-02",
            },
            *[
                {
                    "origin_index": 0,
                    "dest_index": last_idx,
                    "distance_km": 1.0,
                    "passenger_id": None,
                }
                for _ in range(6)
            ],
        ],
        "passenger_pool": [tracked_id, "user-through-tracked-02"],
        "current_trip_id": None,
    }

    now = datetime.now(timezone.utc)
    await simulate_passengers_at_stop(db, vehicle, sim_stops, last_idx, state, now)
    await db.flush()

    # Invariant: no tracked passenger_id survives into the new route leg
    surviving_ids = [
        p["passenger_id"]
        for p in state["passengers"]
        if p.get("passenger_id") is not None
    ]
    assert (
        surviving_ids == []
    ), f"Tracked IDs leaked into next route leg: {surviving_ids}"

    # At least one alighted record must exist for the tracked passenger
    rows = (
        await db.scalars(
            select(BoardingRecord).where(
                BoardingRecord.passenger_id == tracked_id,
                BoardingRecord.event_type == "alighted",
            )
        )
    ).all()
    assert len(rows) >= 1, "No alighted record written for tracked through-passenger"
