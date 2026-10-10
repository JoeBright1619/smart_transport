# gps_service/tests/test_orchestrator_sync.py
from __future__ import annotations

from unittest.mock import MagicMock

from gps_service.models.gps_data import VehicleState
from gps_service.simulator.orchestrator import SimulatorOrchestrator


def _vehicle(vid: str) -> VehicleState:
    return VehicleState(
        vehicle_id=vid,
        device_id=f"d-{vid}",
        tenant_id="t1",
        route_id="r1",
        latitude=0.0,
        longitude=0.0,
        speed=0.0,
        heading=0.0,
        status="active",
        engine_status="good",
        fuel=50.0,
        last_updated="2026-01-01T00:00:00Z",
    )


def test_sync_vehicles_adds_and_removes():
    state_manager = MagicMock()
    state_manager.all.return_value = [_vehicle("v1"), _vehicle("v2")]

    orch = SimulatorOrchestrator(
        state_manager=state_manager,
        route_cache=MagicMock(),
        publisher=MagicMock(),
    )

    orch.sync_vehicles([_vehicle("v1"), _vehicle("v3")])

    added_ids = {call.args[0].vehicle_id for call in state_manager.set.call_args_list}
    removed_ids = {call.args[0] for call in state_manager.remove.call_args_list}

    assert added_ids == {"v3"}
    assert removed_ids == {"v2"}
