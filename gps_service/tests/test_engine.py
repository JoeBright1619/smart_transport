from datetime import UTC, datetime

import pytest

from gps_service.models.gps_data import RouteStop, VehicleState
from gps_service.simulator.engine import (
    CONGESTION_SPEED,
    DWELL_TICKS,
    SimulationEngine,
)
from gps_service.simulator.state_manager import SimulationState
from gps_service.simulator.congestion import update_congestion


@pytest.fixture
def engine() -> SimulationEngine:
    return SimulationEngine()


@pytest.fixture
def stops() -> list[RouteStop]:
    return [
        RouteStop(
            stop_id="stop-1",
            latitude=-1.9500,
            longitude=30.0600,
            sequence=0,
        ),
        RouteStop(
            stop_id="stop-2",
            latitude=-1.9550,
            longitude=30.0650,
            sequence=1,
        ),
        RouteStop(
            stop_id="stop-3",
            latitude=-1.9600,
            longitude=30.0700,
            sequence=2,
        ),
    ]


@pytest.fixture
def vehicle() -> VehicleState:
    return VehicleState(
        vehicle_id="vehicle-1",
        device_id="device-1",
        route_id="route-1",
        tenant_id="tenant-1",
        latitude=-1.9500,
        longitude=30.0600,
        speed=0,
        heading=0,
        engine_status="good",
        status="active",
        fuel=100,
        last_updated=datetime.now(UTC),
    )


def test_advance_vehicle_moves_vehicle(
    engine: SimulationEngine,
    vehicle: VehicleState,
    stops: list[RouteStop],
) -> None:
    simulation_state = SimulationState(next_stop_index=1)

    updated = engine.advance_vehicle(
        vehicle,
        stops,
        simulation_state,
    )

    assert updated is vehicle
    assert updated is not None
    assert updated.latitude != -1.9500 or updated.longitude != 30.0600
    assert updated.speed > 0


def test_advance_vehicle_updates_heading(
    engine: SimulationEngine,
    vehicle: VehicleState,
    stops: list[RouteStop],
) -> None:
    simulation_state = SimulationState(next_stop_index=1)

    engine.advance_vehicle(
        vehicle,
        stops,
        simulation_state,
    )

    assert 0 <= vehicle.heading <= 360


def test_advance_vehicle_consumes_fuel(
    engine: SimulationEngine,
    vehicle: VehicleState,
    stops: list[RouteStop],
) -> None:
    simulation_state = SimulationState(next_stop_index=1)
    initial_fuel = vehicle.fuel

    engine.advance_vehicle(
        vehicle,
        stops,
        simulation_state,
    )

    assert vehicle.fuel < initial_fuel
    assert vehicle.fuel >= 0


def test_vehicle_arrives_at_stop(
    engine: SimulationEngine,
    vehicle: VehicleState,
    stops: list[RouteStop],
) -> None:
    # Place the vehicle very close to the target stop so one tick reaches it.
    vehicle.latitude = stops[1].latitude
    vehicle.longitude = stops[1].longitude

    simulation_state = SimulationState(next_stop_index=1)

    engine.advance_vehicle(
        vehicle,
        stops,
        simulation_state,
    )

    assert vehicle.latitude == stops[1].latitude
    assert vehicle.longitude == stops[1].longitude
    assert vehicle.speed == 0
    assert simulation_state.next_stop_index == 2
    assert simulation_state.dwell_remaining == DWELL_TICKS


def test_vehicle_dwells_at_stop(
    engine: SimulationEngine,
    vehicle: VehicleState,
    stops: list[RouteStop],
) -> None:
    simulation_state = SimulationState(
        next_stop_index=1,
        dwell_remaining=2,
    )

    original_latitude = vehicle.latitude
    original_longitude = vehicle.longitude

    engine.advance_vehicle(
        vehicle,
        stops,
        simulation_state,
    )

    assert vehicle.latitude == original_latitude
    assert vehicle.longitude == original_longitude
    assert vehicle.speed == 0
    assert simulation_state.dwell_remaining == 1


def test_vehicle_does_not_move_when_status_is_not_active(
    engine: SimulationEngine,
    vehicle: VehicleState,
    stops: list[RouteStop],
) -> None:
    vehicle.status = "idle"

    simulation_state = SimulationState(next_stop_index=1)

    updated = engine.advance_vehicle(
        vehicle,
        stops,
        simulation_state,
    )

    assert updated is vehicle
    assert vehicle.latitude == -1.9500
    assert vehicle.longitude == 30.0600
    assert vehicle.speed == 0
    assert vehicle.fuel == 100


def test_advance_vehicle_requires_two_stops(
    engine: SimulationEngine,
    vehicle: VehicleState,
) -> None:
    stops = [
        RouteStop(
            stop_id="stop-1",
            latitude=-1.9500,
            longitude=30.0600,
            sequence=0,
        )
    ]

    simulation_state = SimulationState()

    result = engine.advance_vehicle(
        vehicle,
        stops,
        simulation_state,
    )

    assert result is None


def test_congestion_reduces_speed(
    engine: SimulationEngine,
    vehicle: VehicleState,
    stops: list[RouteStop],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "gps_service.simulator.congestion.random",
        lambda: 0.0,
    )

    simulation_state = SimulationState(
        next_stop_index=1,
    )

    engine.advance_vehicle(
        vehicle,
        stops,
        simulation_state,
    )

    assert vehicle.speed == CONGESTION_SPEED
    assert simulation_state.congestion_ticks >= 0


def test_congestion_delay_alert_triggers(
    engine: SimulationEngine,
) -> None:
    simulation_state = SimulationState(
        congestion_ticks=1,
        congestion_run_min=1.95,
        delay_alerted=False,
    )

    in_congestion, delay_crossed = update_congestion(
        simulation_state,
    )

    assert in_congestion is True
    assert delay_crossed is True
    assert simulation_state.delay_alerted is True


def test_congestion_delay_alert_only_triggers_once(
    engine: SimulationEngine,
) -> None:
    simulation_state = SimulationState(
        congestion_ticks=10,
        congestion_run_min=2.0,
        delay_alerted=True,
    )

    _, delay_crossed = update_congestion(
        simulation_state,
    )

    assert delay_crossed is False
