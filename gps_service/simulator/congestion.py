from __future__ import annotations

from random import randint, random

from gps_service.simulator.state_manager import SimulationState

CONGESTION_ENABLED = True
CONGESTION_CHANCE = 0.015
CONGESTION_MIN_TICKS = 24
CONGESTION_MAX_TICKS = 48
CONGESTION_SPEED = 7
TICK_SECONDS = 5
DELAY_ALERT_MINUTES = 2


def update_congestion(
    state: SimulationState,
    *,
    enabled: bool = CONGESTION_ENABLED,
    probability: float = CONGESTION_CHANCE,
) -> tuple[bool, bool]:
    """Advance congestion state by one simulation tick.

    Returns:
        A tuple containing:
        - whether the vehicle is currently in congestion
        - whether the delay alert threshold was crossed this tick
    """

    if not enabled:
        state.congestion_ticks = 0
        state.congestion_run_min = 0.0
        state.delay_alerted = False
        return False, False

    remaining = state.congestion_ticks

    if remaining <= 0 and random() < probability:  # nosec B311
        remaining = randint(
            CONGESTION_MIN_TICKS,
            CONGESTION_MAX_TICKS,
        )  # nosec B311

    if remaining <= 0:
        state.congestion_ticks = 0
        state.congestion_run_min = 0.0
        return False, False

    state.congestion_ticks = remaining - 1
    state.congestion_run_min += TICK_SECONDS / 60

    delay_crossed = False

    if state.congestion_run_min >= DELAY_ALERT_MINUTES and not state.delay_alerted:
        state.delay_alerted = True
        delay_crossed = True

    return True, delay_crossed
