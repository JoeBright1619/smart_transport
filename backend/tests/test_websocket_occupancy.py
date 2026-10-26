"""Tests for Task 13.2 — real-time occupancy broadcast via WebSocket.

Covers:
  - _simulate_passengers_at_stop updates state["current_occupancy"]
  - manager.publish_to_tenant is called with vehicle_occupancy_updated payload
  - tracking broadcast message includes currentOccupancy / seatingCapacity / remainingSeats
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.websocket.route_simulation import StopPoint


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def vehicle(make_vehicle, tenant):
    return await make_vehicle(
        tenant_id=tenant.id,
        status="active",
        lat=-1.9536,
        lng=30.0606,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _make_stops(make_stop, tenant):
    db_stop1 = await make_stop(tenant_id=tenant.id, name="Start")
    db_stop2 = await make_stop(tenant_id=tenant.id, name="Mid")
    db_stop3 = await make_stop(tenant_id=tenant.id, name="End")
    return [
        StopPoint(
            id=db_stop1.id,
            name="Start",
            lat=-1.9536,
            lng=30.0606,
        ),
        StopPoint(
            id=db_stop2.id,
            name="Mid",
            lat=-1.9600,
            lng=30.0700,
        ),
        StopPoint(
            id=db_stop3.id,
            name="End",
            lat=-1.9700,
            lng=30.0800,
        ),
    ]
    return [
        StopPoint(id="s1", name="Start", lat=-1.9536, lng=30.0606),
        StopPoint(id="s2", name="Mid", lat=-1.9600, lng=30.0700),
        StopPoint(id="s3", name="End", lat=-1.9700, lng=30.0800),
    ]


# ---------------------------------------------------------------------------
# Simulation state tests
# ---------------------------------------------------------------------------


async def test_simulate_passengers_updates_current_occupancy(
    db: AsyncSession, vehicle, make_stop, tenant
):
    from app.websocket.passenger_simulation import (
        simulate_passengers_at_stop as _simulate_passengers_at_stop,
    )

    stops = await _make_stops(make_stop, tenant)
    state: dict = {"passengers": [], "current_occupancy": 0}
    now = datetime.now(timezone.utc)

    with patch(
        "app.websocket.passenger_simulation.manager.publish_to_tenant",
        new_callable=AsyncMock,
    ):
        await _simulate_passengers_at_stop(db, vehicle, stops, 0, state, now)

    assert isinstance(state["current_occupancy"], int)
    assert state["current_occupancy"] == len(state["passengers"])


# ---------------------------------------------------------------------------
# Publish payload tests
# ---------------------------------------------------------------------------


async def test_simulate_passengers_publishes_occupancy_event(
    db: AsyncSession, vehicle, make_stop, tenant
):
    from app.websocket.passenger_simulation import (
        simulate_passengers_at_stop as _simulate_passengers_at_stop,
    )

    stops = await _make_stops(make_stop, tenant)
    state: dict = {"passengers": [], "current_occupancy": 0}
    now = datetime.now(timezone.utc)

    with patch(
        "app.websocket.passenger_simulation.manager.publish_to_tenant",
        new_callable=AsyncMock,
    ) as mock_publish:
        await _simulate_passengers_at_stop(db, vehicle, stops, 0, state, now)

    assert mock_publish.called
    # A stop can also publish a capacity 'new_alert', so pick the occupancy event.
    occupancy_calls = [
        c
        for c in mock_publish.call_args_list
        if c[0][1].get("type") == "vehicle_occupancy_updated"
    ]
    assert occupancy_calls
    tenant_id_arg, payload = occupancy_calls[-1][0]
    assert tenant_id_arg == vehicle.tenant_id
    assert payload["type"] == "vehicle_occupancy_updated"
    assert payload["vehicleId"] == vehicle.id
    assert isinstance(payload["currentOccupancy"], int)
    assert isinstance(payload["seatingCapacity"], int)
    assert isinstance(payload["remainingSeats"], int)
    assert payload["seatingCapacity"] == vehicle.seating_capacity
    # Remaining seats floor at zero — an overcrowded bus reports 0, not a negative.
    assert payload["remainingSeats"] == max(
        0, payload["seatingCapacity"] - payload["currentOccupancy"]
    )


async def test_simulate_passengers_publishes_correct_remaining_seats(
    db: AsyncSession, vehicle, make_stop, tenant
):
    from app.websocket.passenger_simulation import (
        simulate_passengers_at_stop as _simulate_passengers_at_stop,
    )

    stops = await _make_stops(make_stop, tenant)
    state: dict = {"passengers": [], "current_occupancy": 0}
    now = datetime.now(timezone.utc)

    with patch(
        "app.websocket.passenger_simulation.manager.publish_to_tenant",
        new_callable=AsyncMock,
    ) as mock_publish:
        await _simulate_passengers_at_stop(db, vehicle, stops, 0, state, now)

    occupancy_calls = [
        c
        for c in mock_publish.call_args_list
        if c[0][1].get("type") == "vehicle_occupancy_updated"
    ]
    payload = occupancy_calls[-1][0][1]
    expected_remaining = max(
        0, payload["seatingCapacity"] - payload["currentOccupancy"]
    )
    assert payload["remainingSeats"] == expected_remaining


# ---------------------------------------------------------------------------
# Tracking broadcast payload test
# ---------------------------------------------------------------------------


async def test_build_vehicle_update_includes_occupancy_fields(
    db: AsyncSession, tenant, make_vehicle
):
    """_build_vehicle_update_message should include occupancy keys per vehicle.

    Patches AsyncSessionLocal so the function queries the test's in-memory DB.
    """
    from contextlib import asynccontextmanager

    from app.websocket import tracking
    from app.websocket.route_simulation import _state

    vehicle = await make_vehicle(
        tenant_id=tenant.id,
        status="active",
        lat=-1.9536,
        lng=30.0606,
    )

    # Pre-seed simulation state
    _state[vehicle.id] = {
        "next_stop_index": 1,
        "current_occupancy": 12,
        "passengers": [{}] * 12,
        "fuel_pct": 80.0,
        "loop_count": 0,
        "trip_started_at": datetime.now(timezone.utc),
    }

    @asynccontextmanager
    async def _mock_session():
        yield db

    try:
        with patch("app.websocket.tracking.AsyncSessionLocal", _mock_session):
            message = await tracking._build_vehicle_update_message(tenant.id)
    finally:
        _state.pop(vehicle.id, None)

    assert message["type"] == "vehicle_update"
    assert len(message["data"]) >= 1
    entry = next(v for v in message["data"] if v["vehicleId"] == vehicle.id)
    assert "currentOccupancy" in entry
    assert "seatingCapacity" in entry
    assert "remainingSeats" in entry
    assert entry["currentOccupancy"] == 12
    assert entry["seatingCapacity"] == vehicle.seating_capacity
    assert entry["remainingSeats"] == vehicle.seating_capacity - 12


# ---------------------------------------------------------------------------
# Task 1.1 — Realistic boarding cap + DB persistence tests
# ---------------------------------------------------------------------------


async def test_vehicle_current_occupancy_persisted_to_db(
    db: AsyncSession, vehicle, make_stop, tenant
):
    """vehicle.current_occupancy must be set to match in-memory state after a tick."""
    from sqlalchemy import select

    from app.models.vehicle import Vehicle
    from app.websocket.passenger_simulation import (
        simulate_passengers_at_stop as _simulate_passengers_at_stop,
    )

    # Create actual rows in the stops table.
    stops = await _make_stops(make_stop, tenant)

    state: dict = {"passengers": [], "current_occupancy": 0}
    now = datetime.now(timezone.utc)

    with patch(
        "app.websocket.passenger_simulation.manager.publish_to_tenant",
        new_callable=AsyncMock,
    ):
        await _simulate_passengers_at_stop(db, vehicle, stops, 0, state, now)

    # Refresh from DB to confirm the flush wrote the value
    fresh = await db.scalar(select(Vehicle).where(Vehicle.id == vehicle.id))
    assert fresh is not None
    assert fresh.current_occupancy == state["current_occupancy"]
    assert fresh.current_occupancy == len(state["passengers"])
