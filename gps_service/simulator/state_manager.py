from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from gps_service.models.gps_data import VehicleState


@dataclass
class SimulationState:
    next_stop_index: int = 1
    dwell_remaining: int = 0
    congestion_ticks: int = 0
    congestion_run_min: float = 0.0
    delay_alerted: bool = False


class VehicleStateManager:
    """Manage in-memory vehicle state with local persistence."""

    def __init__(self, state_file: str = "gps_service/state/vehicles.json") -> None:
        self.state_file = Path(state_file)
        self.states: dict[str, VehicleState] = {}
        self.simulation_states: dict[str, SimulationState] = {}
        self._load()

    def get(self, vehicle_id: str) -> VehicleState | None:
        """Get the current state for a vehicle."""
        return self.states.get(vehicle_id)

    def set(self, state: VehicleState) -> None:
        """Create or replace the state for a vehicle."""
        self.states[state.vehicle_id] = state

    def update(
        self,
        vehicle_id: str,
        **updates: Any,
    ) -> VehicleState:
        """Update selected fields of an existing vehicle state."""
        state = self.states.get(vehicle_id)

        if state is None:
            raise KeyError(f"Vehicle state not found: {vehicle_id}")

        updated_state = state.model_copy(update=updates)
        self.states[vehicle_id] = updated_state

        return updated_state

    def remove(self, vehicle_id: str) -> None:
        """Remove a vehicle from the state manager."""
        self.states.pop(vehicle_id, None)
        self.simulation_states.pop(vehicle_id, None)

    def all(self) -> list[VehicleState]:
        """Return all tracked vehicle states."""
        return list(self.states.values())

    def save(self) -> None:
        """Persist current vehicle states to disk."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            vehicle_id: state.model_dump(mode="json")
            for vehicle_id, state in self.states.items()
        }

        self.state_file.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8",
        )

    def _load(self) -> None:
        """Recover vehicle states from disk if a state file exists."""
        if not self.state_file.exists():
            return

        try:
            data = json.loads(self.state_file.read_text(encoding="utf-8"))

            self.states = {
                vehicle_id: VehicleState.model_validate(state)
                for vehicle_id, state in data.items()
            }

        except (json.JSONDecodeError, ValueError):
            self.states = {}

    def get_simulation_state(self, vehicle_id: str) -> SimulationState:
        state = self.simulation_states.get(vehicle_id)

        if state is None:
            state = SimulationState()
            self.simulation_states[vehicle_id] = state

        return state
