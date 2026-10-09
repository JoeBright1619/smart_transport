from datetime import datetime, timezone

from gps_service.models.gps_data import VehicleState
from gps_service.simulator.state_manager import VehicleStateManager


def create_vehicle_state() -> VehicleState:
    return VehicleState(
        vehicle_id="vehicle-001",
        device_id="device-001",
        tenant_id="tenant-001",
        route_id="route-001",
        latitude=-1.9441,
        longitude=30.0585,
        speed=30.0,
        heading=90.0,
        status="active",
        engine_status="good",
        fuel=85.0,
        last_updated=datetime.now(timezone.utc),
    )


def test_set_and_get_state(tmp_path):
    manager = VehicleStateManager(state_file=str(tmp_path / "vehicles.json"))

    state = create_vehicle_state()

    manager.set(state)

    assert manager.get("vehicle-001") == state


def test_update_state(tmp_path):
    manager = VehicleStateManager(state_file=str(tmp_path / "vehicles.json"))

    manager.set(create_vehicle_state())

    updated = manager.update(
        "vehicle-001",
        speed=45.0,
        fuel=80.0,
    )

    assert updated.speed == 45.0
    assert updated.fuel == 80.0
    assert updated.latitude == -1.9441


def test_remove_state(tmp_path):
    manager = VehicleStateManager(state_file=str(tmp_path / "vehicles.json"))

    manager.set(create_vehicle_state())
    manager.remove("vehicle-001")

    assert manager.get("vehicle-001") is None


def test_state_persistence_and_recovery(tmp_path):
    state_file = tmp_path / "vehicles.json"

    manager = VehicleStateManager(state_file=str(state_file))
    state = create_vehicle_state()

    manager.set(state)
    manager.save()

    recovered_manager = VehicleStateManager(state_file=str(state_file))

    recovered = recovered_manager.get("vehicle-001")

    assert recovered == state
