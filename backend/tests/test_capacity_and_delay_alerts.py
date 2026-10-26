"""Tests that the capacity and delay alerts can actually be triggered by the simulation.

Capacity: a terminal can now overcrowd past seated capacity, which raises a capacity alert.
Delay: a sustained traffic jam crosses the delay threshold once per journey.
"""

from __future__ import annotations

from unittest.mock import patch


from app.websocket import route_simulation as rs

_MGR = "app.websocket.manager.manager.publish_to_tenant"


# ---------------------------------------------------------------------------
# Capacity
# ---------------------------------------------------------------------------


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
