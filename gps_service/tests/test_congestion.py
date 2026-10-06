from gps_service.simulator.congestion import (
    CONGESTION_MAX_TICKS,
    CONGESTION_MIN_TICKS,
    update_congestion,
)
from gps_service.simulator.state_manager import SimulationState


def test_congestion_can_be_disabled() -> None:
    state = SimulationState(
        congestion_ticks=10,
        congestion_run_min=1.0,
        delay_alerted=True,
    )

    in_congestion, delay_crossed = update_congestion(
        state,
        enabled=False,
    )

    assert in_congestion is False
    assert delay_crossed is False
    assert state.congestion_ticks == 0
    assert state.congestion_run_min == 0.0
    assert state.delay_alerted is False


def test_congestion_starts_when_probability_triggers(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "gps_service.simulator.congestion.random",
        lambda: 0.0,
    )

    state = SimulationState()

    in_congestion, delay_crossed = update_congestion(
        state,
        probability=0.015,
    )

    assert in_congestion is True
    assert delay_crossed is False
    assert 0 <= state.congestion_ticks < CONGESTION_MAX_TICKS


def test_congestion_does_not_start_when_probability_does_not_trigger(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "gps_service.simulator.congestion.random",
        lambda: 1.0,
    )

    state = SimulationState()

    in_congestion, delay_crossed = update_congestion(
        state,
        probability=0.015,
    )

    assert in_congestion is False
    assert delay_crossed is False
    assert state.congestion_ticks == 0


def test_existing_congestion_continues() -> None:
    state = SimulationState(
        congestion_ticks=5,
    )

    in_congestion, delay_crossed = update_congestion(
        state,
    )

    assert in_congestion is True
    assert delay_crossed is False
    assert state.congestion_ticks == 4


def test_congestion_duration_is_within_configured_range(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "gps_service.simulator.congestion.random",
        lambda: 0.0,
    )

    state = SimulationState()

    update_congestion(state)

    assert CONGESTION_MIN_TICKS - 1 <= state.congestion_ticks < CONGESTION_MAX_TICKS


def test_delay_alert_triggers_after_threshold() -> None:
    state = SimulationState(
        congestion_ticks=1,
        congestion_run_min=1.95,
        delay_alerted=False,
    )

    in_congestion, delay_crossed = update_congestion(state)

    assert in_congestion is True
    assert delay_crossed is True
    assert state.delay_alerted is True


def test_delay_alert_only_triggers_once() -> None:
    state = SimulationState(
        congestion_ticks=10,
        congestion_run_min=2.0,
        delay_alerted=True,
    )

    _, delay_crossed = update_congestion(state)

    assert delay_crossed is False
    assert state.delay_alerted is True
