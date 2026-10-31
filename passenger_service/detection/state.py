"""Per-vehicle arrival state and the store that owns it.

Mirrors design §3 "Per-vehicle state" and "VehicleStateStore". The store
is the only mutable owner of per-vehicle state in passenger_service; the
detector (§3) and simulation (§7) take a `VehicleArrivalState` by
argument and never mutate the store themselves.

Not thread-safe: passenger_service runs on a single asyncio event loop
(see project context), so all mutations happen on that loop's thread.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class VehicleArrivalState:
    """Per-vehicle state carried across position events.

    Field set matches design §3's `VehicleArrivalState` exactly. Notably
    absent:

    - `vehicle_id` — the store keys by id; the state doesn't carry one.
    - `passenger_pool` — the pool is universal and process-wide; it is
      passed to the simulation as an argument (§7), never stored here.
    """

    route_id: str | None = None
    last_lat: float | None = None
    last_lng: float | None = None
    last_speed: float | None = None
    last_stop_id: str | None = None
    last_arrival_ts: float | None = None  # monotonic seconds
    armed: bool = True
    arrival_sequence: int = 0
    onboard: int = 0
    needs_synthesis: bool = False
    last_position_ts: datetime | None = None
    passengers: list[dict] = field(default_factory=list)
    current_trip_id: str | None = None


@dataclass(frozen=True)
class VehicleSeed:
    """Initial values for a vehicle's first appearance.

    Fetched from the backend once per vehicle: `arrival_sequence` from
    GET /api/v1/service/vehicles/{id}/latest-arrival-sequence, `onboard`
    from `current_occupancy` in GET /api/v1/service/vehicles?status=active.
    """

    arrival_sequence: int = 0
    onboard: int = 0


@dataclass(frozen=True)
class StateLookup:
    """Return value of VehicleStateStore.get_or_create().

    `state` is the (mutable) state for the vehicle. `released_ids` are
    the real passenger IDs that were on board before a route change or
    removal, so the caller can free them from the process-wide set.
    Empty on same-route calls and on new vehicles.
    """

    state: VehicleArrivalState
    released_ids: list[str] = field(default_factory=list)


def _real_ids(state: VehicleArrivalState) -> list[str]:
    """Return the real passenger IDs currently on board.

    Per §7's per-passenger record, `passenger_id` is None for anonymous
    (synthesised or through-) passengers. Real-vs-anonymous is
    discriminated on that field, not on a separate flag.
    """

    return [p["passenger_id"] for p in state.passengers if p.get("passenger_id")]


class VehicleStateStore:
    """Dict-backed store of per-vehicle state. Keyed by vehicle_id.

    No persistence to disk or Redis (design §3: "no persistence to disk
    or Redis"). Rebuilt from the backend on restart via VehicleSeed.
    """

    def __init__(self) -> None:
        self._by_vehicle: dict[str, VehicleArrivalState] = {}

    def has(self, vehicle_id: str) -> bool:
        return vehicle_id in self._by_vehicle

    def get_or_create(
        self,
        vehicle_id: str,
        route_id: str,
        seed: VehicleSeed | None = None,
    ) -> StateLookup:
        existing = self._by_vehicle.get(vehicle_id)

        if existing is None:
            effective_seed = seed or VehicleSeed()
            state = VehicleArrivalState(
                route_id=route_id,
                arrival_sequence=effective_seed.arrival_sequence,
                onboard=effective_seed.onboard,
                needs_synthesis=effective_seed.onboard > 0,
            )
            self._by_vehicle[vehicle_id] = state
            return StateLookup(state=state, released_ids=[])

        if existing.route_id != route_id:
            released = _real_ids(existing)
            # Preserve cross-route carried state that must survive a
            # route change: arrival_sequence is monotonically increasing
            # per vehicle (§4 — resetting it would collide idempotency
            # keys); onboard carries the true count so synthesis kicks in.
            existing.route_id = route_id
            existing.last_stop_id = None
            existing.last_arrival_ts = None
            existing.last_lat = None
            existing.last_lng = None
            existing.last_speed = None
            existing.last_position_ts = None
            existing.armed = True
            existing.passengers = []
            existing.needs_synthesis = existing.onboard > 0
            return StateLookup(state=existing, released_ids=released)

        return StateLookup(state=existing, released_ids=[])

    def remove(self, vehicle_id: str) -> list[str]:
        """Drop the vehicle's state and return its real passenger IDs.

        Returns [] for unknown vehicles (no raise — the periodic refresh
        may race with detection and call remove for a vehicle that was
        never seen).
        """

        state = self._by_vehicle.pop(vehicle_id, None)
        if state is None:
            return []
        return _real_ids(state)
