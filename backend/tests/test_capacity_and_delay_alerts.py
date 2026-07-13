"""Tests that the capacity and delay alerts can actually be triggered by the simulation.

Capacity: a terminal can now overcrowd past seated capacity, which raises a capacity alert.
Delay: a sustained traffic jam crosses the delay threshold once per journey.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select

from app.models.alert import Alert
from app.websocket import passenger_simulation
from app.websocket import route_simulation as rs
from app.websocket.route_simulation import StopPoint

_MGR = "app.websocket.manager.manager.publish_to_tenant"


@pytest.fixture
async def tenant(make_tenant):
    return await make_tenant()


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Capacity
# ---------------------------------------------------------------------------


async def test_terminal_overcrowd_raises_capacity_alert(db, make_vehicle, tenant):
    vehicle = await make_vehicle(tenant_id=tenant.id, status="active")
    stops = [
        StopPoint(id="s0", name="A", lat=-1.95, lng=30.06),
        StopPoint(id="s1", name="B", lat=-1.96, lng=30.07),
        StopPoint(id="s2", name="C", lat=-1.97, lng=30.08),
    ]

    # Force the terminal boarding to the top of its range (overcrowd). Patching randint to
    # return its upper bound keeps every other draw (dest index, etc.) in range too.
    with (
        patch(_MGR, new=AsyncMock()),
        patch("app.websocket.passenger_simulation.randint", side_effect=lambda a, b: b),
    ):
        await passenger_simulation.simulate_passengers_at_stop(
            db, vehicle, stops, 0, {}, _now()
        )

    assert vehicle.current_occupancy >= vehicle.seating_capacity
    alerts = (
        await db.scalars(
            select(Alert).where(
                Alert.vehicle_id == vehicle.id, Alert.type == "capacity"
            )
        )
    ).all()
    assert len(alerts) >= 1


# ---------------------------------------------------------------------------
# Delay (traffic congestion)
# ---------------------------------------------------------------------------


def test_sustained_congestion_crosses_delay_threshold_once():
    state: dict = {}
    ticks_for_threshold = int(rs.DELAY_ALERT_MINUTES * 60 / rs.TICK_SECONDS)

    crosses = 0
    # Always enter congestion, and make the jam long enough to outlast the threshold.
    with (
        patch("app.websocket.route_simulation.random", return_value=0.0),
        patch(
            "app.websocket.route_simulation.randint",
            return_value=rs.CONGESTION_MAX_TICKS,
        ),
    ):
        for _ in range(ticks_for_threshold + 5):
            in_congestion, delay_crossed = rs._update_congestion(state)
            assert in_congestion is True
            if delay_crossed:
                crosses += 1

    assert crosses == 1  # fires exactly once per journey


def test_no_congestion_when_chance_not_met():
    state: dict = {}
    with patch("app.websocket.route_simulation.random", return_value=1.0):
        in_congestion, delay_crossed = rs._update_congestion(state)
    assert in_congestion is False
    assert delay_crossed is False
    assert state["congestion_ticks"] == 0
