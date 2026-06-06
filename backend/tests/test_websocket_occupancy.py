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


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def tenant(make_tenant):
    return await make_tenant()


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


def _make_stops():
    from app.websocket.route_simulation import StopPoint

    return [
        StopPoint(id="s1", name="Start", lat=-1.9536, lng=30.0606),
        StopPoint(id="s2", name="Mid", lat=-1.9600, lng=30.0700),
        StopPoint(id="s3", name="End", lat=-1.9700, lng=30.0800),
    ]


# ---------------------------------------------------------------------------
# Simulation state tests
# ---------------------------------------------------------------------------


async def test_simulate_passengers_updates_current_occupancy(db: AsyncSession, vehicle):
    from app.websocket.route_simulation import _simulate_passengers_at_stop

    stops = _make_stops()
    state: dict = {"passengers": [], "current_occupancy": 0}
    now = datetime.now(timezone.utc)

    with patch(
        "app.websocket.route_simulation.manager.publish_to_tenant",
        new_callable=AsyncMock,
    ):
        await _simulate_passengers_at_stop(db, vehicle, stops, 0, state, now)

    assert isinstance(state["current_occupancy"], int)
    assert state["current_occupancy"] == len(state["passengers"])


async def test_simulate_passengers_occupancy_does_not_exceed_capacity(
    db: AsyncSession, vehicle
):
    from app.websocket.route_simulation import _simulate_passengers_at_stop

    stops = _make_stops()
    state: dict = {"passengers": [], "current_occupancy": 0}
    now = datetime.now(timezone.utc)

    with patch(
        "app.websocket.route_simulation.manager.publish_to_tenant",
        new_callable=AsyncMock,
    ):
        for stop_idx in range(len(stops) - 1):
            await _simulate_passengers_at_stop(db, vehicle, stops, stop_idx, state, now)

    assert state["current_occupancy"] <= vehicle.seating_capacity


# ---------------------------------------------------------------------------
# Publish payload tests
# ---------------------------------------------------------------------------


async def test_simulate_passengers_publishes_occupancy_event(db: AsyncSession, vehicle):
    from app.websocket.route_simulation import _simulate_passengers_at_stop

    stops = _make_stops()
    state: dict = {"passengers": [], "current_occupancy": 0}
    now = datetime.now(timezone.utc)

    with patch(
        "app.websocket.route_simulation.manager.publish_to_tenant",
        new_callable=AsyncMock,
    ) as mock_publish:
        await _simulate_passengers_at_stop(db, vehicle, stops, 0, state, now)

    assert mock_publish.called
    call_args = mock_publish.call_args
    tenant_id_arg, payload = call_args[0]
    assert tenant_id_arg == vehicle.tenant_id
    assert payload["type"] == "vehicle_occupancy_updated"
    assert payload["vehicleId"] == vehicle.id
    assert isinstance(payload["currentOccupancy"], int)
    assert isinstance(payload["seatingCapacity"], int)
    assert isinstance(payload["remainingSeats"], int)
    assert payload["seatingCapacity"] == vehicle.seating_capacity
    assert (
        payload["remainingSeats"]
        == payload["seatingCapacity"] - payload["currentOccupancy"]
    )


async def test_simulate_passengers_publishes_correct_remaining_seats(
    db: AsyncSession, vehicle
):
    from app.websocket.route_simulation import _simulate_passengers_at_stop

    stops = _make_stops()
    state: dict = {"passengers": [], "current_occupancy": 0}
    now = datetime.now(timezone.utc)

    with patch(
        "app.websocket.route_simulation.manager.publish_to_tenant",
        new_callable=AsyncMock,
    ) as mock_publish:
        await _simulate_passengers_at_stop(db, vehicle, stops, 0, state, now)

    payload = mock_publish.call_args[0][1]
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


async def test_boarding_count_never_exceeds_seating_capacity(db: AsyncSession, vehicle):
    """After many stops, on-board passenger count must stay within seating capacity."""
    from app.websocket.route_simulation import _simulate_passengers_at_stop

    stops = _make_stops()
    state: dict = {"passengers": [], "current_occupancy": 0}
    now = datetime.now(timezone.utc)

    with patch(
        "app.websocket.route_simulation.manager.publish_to_tenant",
        new_callable=AsyncMock,
    ):
        for _ in range(20):
            for stop_idx in range(len(stops) - 1):
                await _simulate_passengers_at_stop(
                    db, vehicle, stops, stop_idx, state, now
                )

    on_board = len(state["passengers"])
    assert on_board >= 0
    assert on_board <= vehicle.seating_capacity


async def test_alighting_never_makes_occupancy_negative(db: AsyncSession, vehicle):
    """Occupancy must never go below zero after alighting."""
    from app.websocket.route_simulation import _simulate_passengers_at_stop

    stops = _make_stops()
    state: dict = {"passengers": [], "current_occupancy": 0}
    now = datetime.now(timezone.utc)

    with patch(
        "app.websocket.route_simulation.manager.publish_to_tenant",
        new_callable=AsyncMock,
    ):
        for stop_idx in range(len(stops)):
            await _simulate_passengers_at_stop(db, vehicle, stops, stop_idx, state, now)
            assert state["current_occupancy"] >= 0


async def test_vehicle_current_occupancy_persisted_to_db(db: AsyncSession, vehicle):
    """vehicle.current_occupancy must be set to match in-memory state after a tick."""
    from sqlalchemy import select

    from app.models.vehicle import Vehicle
    from app.websocket.route_simulation import _simulate_passengers_at_stop

    stops = _make_stops()
    state: dict = {"passengers": [], "current_occupancy": 0}
    now = datetime.now(timezone.utc)

    with patch(
        "app.websocket.route_simulation.manager.publish_to_tenant",
        new_callable=AsyncMock,
    ):
        await _simulate_passengers_at_stop(db, vehicle, stops, 0, state, now)

    # Refresh from DB to confirm the flush wrote the value
    fresh = await db.scalar(select(Vehicle).where(Vehicle.id == vehicle.id))
    assert fresh is not None
    assert fresh.current_occupancy == state["current_occupancy"]
    assert fresh.current_occupancy == len(state["passengers"])
