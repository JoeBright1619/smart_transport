from __future__ import annotations
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock

import pytest

from gps_service.models.gps_data import RouteStop, VehicleState
from gps_service.simulator.engine import SimulationEngine
from gps_service.simulator.orchestrator import SimulatorOrchestrator
from gps_service.simulator.state_manager import SimulationState


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
        engine_status=True,
        fuel=100,
        last_updated=datetime.now(UTC),
    )


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
    ]


@pytest.mark.asyncio
async def test_tick_advances_and_publishes_vehicle(
    vehicle: VehicleState,
    stops: list[RouteStop],
) -> None:
    state_manager = Mock()
    state_manager.all.return_value = [vehicle]
    state_manager.get.return_value = vehicle
    state_manager.get_simulation_state.return_value = SimulationState(
        next_stop_index=1,
    )

    route_cache = Mock()
    route_cache.get_route_stops = AsyncMock(return_value=stops)

    publisher = Mock()

    engine = Mock(spec=SimulationEngine)
    engine.advance_vehicle.return_value = vehicle

    orchestrator = SimulatorOrchestrator(
        state_manager=state_manager,
        route_cache=route_cache,
        publisher=publisher,
        engine=engine,
        backend_token="test-token",
    )

    await orchestrator.tick()

    route_cache.get_route_stops.assert_awaited_once_with(
        "route-1",
        "test-token",
    )

    engine.advance_vehicle.assert_called_once()

    state_manager.set.assert_called_once_with(vehicle)

    publisher.publish.assert_called_once()


@pytest.mark.asyncio
async def test_tick_publishes_to_correct_topic(
    vehicle: VehicleState,
    stops: list[RouteStop],
) -> None:
    state_manager = Mock()
    state_manager.all.return_value = [vehicle]
    state_manager.get.return_value = vehicle
    state_manager.get_simulation_state.return_value = SimulationState(
        next_stop_index=1,
    )

    route_cache = Mock()
    route_cache.get_route_stops = AsyncMock(return_value=stops)

    publisher = Mock()

    engine = Mock(spec=SimulationEngine)
    engine.advance_vehicle.return_value = vehicle

    orchestrator = SimulatorOrchestrator(
        state_manager=state_manager,
        route_cache=route_cache,
        publisher=publisher,
        engine=engine,
        backend_token="test-token",
    )

    await orchestrator.tick()

    publish_call = publisher.publish.call_args

    assert publish_call.kwargs["topic"] == ("gps/tenant-1/vehicle-1/position")


@pytest.mark.asyncio
async def test_tick_publishes_gps_position_payload(
    vehicle: VehicleState,
    stops: list[RouteStop],
) -> None:
    state_manager = Mock()
    state_manager.all.return_value = [vehicle]
    state_manager.get.return_value = vehicle
    state_manager.get_simulation_state.return_value = SimulationState(
        next_stop_index=1,
    )

    route_cache = Mock()
    route_cache.get_route_stops = AsyncMock(return_value=stops)

    publisher = Mock()

    engine = Mock(spec=SimulationEngine)
    engine.advance_vehicle.return_value = vehicle

    orchestrator = SimulatorOrchestrator(
        state_manager=state_manager,
        route_cache=route_cache,
        publisher=publisher,
        engine=engine,
        backend_token="test-token",
    )

    await orchestrator.tick()

    publish_call = publisher.publish.call_args
    payload = publish_call.kwargs["payload"]

    assert payload["vehicle_id"] == "vehicle-1"
    assert payload["device_id"] == "device-1"
    assert payload["latitude"] == vehicle.latitude
    assert payload["longitude"] == vehicle.longitude
    assert payload["speed"] == vehicle.speed
    assert payload["heading"] == vehicle.heading
    assert isinstance(payload["timestamp"], str)


@pytest.mark.asyncio
async def test_tick_publishes_with_qos_1(
    vehicle: VehicleState,
    stops: list[RouteStop],
) -> None:
    state_manager = Mock()
    state_manager.all.return_value = [vehicle]
    state_manager.get.return_value = vehicle
    state_manager.get_simulation_state.return_value = SimulationState(
        next_stop_index=1,
    )

    route_cache = Mock()
    route_cache.get_route_stops = AsyncMock(return_value=stops)

    publisher = Mock()

    engine = Mock(spec=SimulationEngine)
    engine.advance_vehicle.return_value = vehicle

    orchestrator = SimulatorOrchestrator(
        state_manager=state_manager,
        route_cache=route_cache,
        publisher=publisher,
        engine=engine,
    )

    await orchestrator.tick()

    publish_call = publisher.publish.call_args

    assert publish_call.kwargs["qos"] == 1


@pytest.mark.asyncio
async def test_tick_skips_inactive_vehicle(
    vehicle: VehicleState,
) -> None:
    vehicle.engine_status = False

    state_manager = Mock()
    state_manager.all.return_value = [vehicle]

    route_cache = Mock()
    route_cache.get_route_stops = AsyncMock()

    publisher = Mock()

    engine = Mock(spec=SimulationEngine)

    orchestrator = SimulatorOrchestrator(
        state_manager=state_manager,
        route_cache=route_cache,
        publisher=publisher,
        engine=engine,
    )

    await orchestrator.tick()

    route_cache.get_route_stops.assert_not_awaited()
    publisher.publish.assert_not_called()
    engine.advance_vehicle.assert_not_called()


@pytest.mark.asyncio
async def test_tick_skips_vehicle_without_enough_stops(
    vehicle: VehicleState,
) -> None:
    state_manager = Mock()
    state_manager.all.return_value = [vehicle]

    route_cache = Mock()
    route_cache.get_route_stops = AsyncMock(
        return_value=[
            RouteStop(
                stop_id="stop-1",
                latitude=-1.9500,
                longitude=30.0600,
                sequence=0,
            )
        ],
    )

    publisher = Mock()

    engine = Mock(spec=SimulationEngine)

    orchestrator = SimulatorOrchestrator(
        state_manager=state_manager,
        route_cache=route_cache,
        publisher=publisher,
        engine=engine,
    )

    await orchestrator.tick()

    engine.advance_vehicle.assert_not_called()
    publisher.publish.assert_not_called()


@pytest.mark.asyncio
async def test_tick_continues_when_one_vehicle_fails(
    vehicle: VehicleState,
    stops: list[RouteStop],
) -> None:
    second_vehicle = vehicle.model_copy(
        update={"vehicle_id": "vehicle-2"},
    )

    state_manager = Mock()
    state_manager.all.return_value = [
        vehicle,
        second_vehicle,
    ]
    state_manager.get.side_effect = [
        vehicle,
        second_vehicle,
    ]
    state_manager.get_simulation_state.return_value = SimulationState(
        next_stop_index=1,
    )

    route_cache = Mock()
    route_cache.get_route_stops = AsyncMock(return_value=stops)

    publisher = Mock()

    engine = Mock(spec=SimulationEngine)
    engine.advance_vehicle.side_effect = [
        RuntimeError("simulation error"),
        second_vehicle,
    ]

    orchestrator = SimulatorOrchestrator(
        state_manager=state_manager,
        route_cache=route_cache,
        publisher=publisher,
        engine=engine,
    )

    await orchestrator.tick()

    assert publisher.publish.call_count == 1
    state_manager.set.assert_called_once_with(second_vehicle)


@pytest.mark.asyncio
async def test_mqtt_publish_retries_after_failure(
    vehicle: VehicleState,
    stops: list[RouteStop],
) -> None:
    state_manager = Mock()
    state_manager.all.return_value = [vehicle]
    state_manager.get.return_value = vehicle
    state_manager.get_simulation_state.return_value = SimulationState(
        next_stop_index=1,
    )

    route_cache = Mock()
    route_cache.get_route_stops = AsyncMock(return_value=stops)

    publisher = Mock()
    publisher.publish.side_effect = [
        RuntimeError("broker unavailable"),
        None,
    ]

    engine = Mock(spec=SimulationEngine)
    engine.advance_vehicle.return_value = vehicle

    orchestrator = SimulatorOrchestrator(
        state_manager=state_manager,
        route_cache=route_cache,
        publisher=publisher,
        engine=engine,
        backend_token="test-token",
    )

    await orchestrator.tick()

    assert publisher.publish.call_count == 2

    final_call = publisher.publish.call_args
    assert final_call.kwargs["topic"] == "gps/tenant-1/vehicle-1/position"
    assert final_call.kwargs["qos"] == 1


@pytest.mark.asyncio
async def test_mqtt_publish_stops_after_max_retries(
    vehicle: VehicleState,
    stops: list[RouteStop],
) -> None:
    state_manager = Mock()
    state_manager.all.return_value = [vehicle]
    state_manager.get.return_value = vehicle
    state_manager.get_simulation_state.return_value = SimulationState(
        next_stop_index=1,
    )

    route_cache = Mock()
    route_cache.get_route_stops = AsyncMock(return_value=stops)

    publisher = Mock()
    publisher.publish.side_effect = RuntimeError("broker unavailable")

    engine = Mock(spec=SimulationEngine)
    engine.advance_vehicle.return_value = vehicle

    orchestrator = SimulatorOrchestrator(
        state_manager=state_manager,
        route_cache=route_cache,
        publisher=publisher,
        engine=engine,
        backend_token="test-token",
    )

    await orchestrator.tick()

    assert publisher.publish.call_count == 3


@pytest.mark.asyncio
async def test_route_fetch_failure_skips_vehicle(
    vehicle: VehicleState,
    stops: list[RouteStop],
) -> None:
    second_vehicle = vehicle.model_copy(
        update={"vehicle_id": "vehicle-2"},
    )

    state_manager = Mock()
    state_manager.all.return_value = [
        vehicle,
        second_vehicle,
    ]
    state_manager.get.side_effect = [
        vehicle,
        second_vehicle,
    ]
    state_manager.get_simulation_state.return_value = SimulationState(
        next_stop_index=1,
    )

    route_cache = Mock()
    route_cache.get_route_stops = AsyncMock(
        side_effect=[
            RuntimeError("backend unavailable"),
            stops,
        ],
    )

    publisher = Mock()

    engine = Mock(spec=SimulationEngine)
    engine.advance_vehicle.return_value = second_vehicle

    orchestrator = SimulatorOrchestrator(
        state_manager=state_manager,
        route_cache=route_cache,
        publisher=publisher,
        engine=engine,
        backend_token="test-token",
    )

    await orchestrator.tick()

    assert route_cache.get_route_stops.await_count == 2
    assert engine.advance_vehicle.call_count == 1
    assert publisher.publish.call_count == 1

    engine.advance_vehicle.assert_called_once()
    publisher.publish.assert_called_once()
