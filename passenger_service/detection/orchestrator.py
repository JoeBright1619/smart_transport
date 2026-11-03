"""Stop-arrival detection orchestrator (design §3).

The only component that mutates `VehicleArrivalState` and the
process-wide `_globally_on_board` set. Pure components (detect_arrival,
simulate_passengers) are called by this class; the orchestrator applies
their results.

No MQTT wiring, no timers, no threads. `handle_position` takes a parsed
`PositionEvent` and returns the published `OccupancyEvent` (or `None`).
The caller owns scheduling, publishing, and the periodic vehicle-map
refresh (which calls `set_vehicle_map`).
"""

from __future__ import annotations

import logging
import time
from typing import Mapping

from passenger_service.config import PassengerServiceSettings
from passenger_service.detection.detector import detect_arrival
from passenger_service.detection.state import (
    VehicleArrivalState,
    VehicleSeed,
    VehicleStateStore,
)
from passenger_service.geo import haversine_distance
from passenger_service.models.occupancy import OccupancyEvent, build_occupancy_event
from passenger_service.models.position import PositionEvent
from passenger_service.models.route_stop import RouteStop
from passenger_service.models.vehicle_info import VehicleInfo
from passenger_service.route_cache.cache import RouteCache
from passenger_service.simulation.engine import (
    SimulationParams,
    make_rng,
    simulate_passengers,
)
from passenger_service.vehicle_map.sequence_client import SequenceClient

logger = logging.getLogger(__name__)


class ArrivalOrchestrator:
    """Runs the detection loop for each inbound position event."""

    def __init__(
        self,
        *,
        state_store: VehicleStateStore,
        route_cache: RouteCache,
        sequence_client: SequenceClient,
        pool_fetcher,  # PassengerPoolFetcher; typed loosely to avoid a circular-ish import
        publisher,  # mqtt publisher; typed loosely (duck-typed .publish)
        settings: PassengerServiceSettings,
        service_token: str,
    ) -> None:
        self._state_store = state_store
        self._route_cache = route_cache
        self._sequence_client = sequence_client
        self._pool_fetcher = pool_fetcher
        self._publisher = publisher
        self._settings = settings
        self._service_token = service_token

        self._vehicle_map: dict[str, VehicleInfo] = {}
        self._globally_on_board: set[str] = set()

        # Simulation params are fixed for the process lifetime.
        self._sim_params = SimulationParams(
            crush_capacity_factor=settings.CRUSH_CAPACITY_FACTOR,
            revenue_per_km=settings.REVENUE_PER_KM,
        )
        self._events_published: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def events_published(self) -> int:
        """Count of occupancy events published since this orchestrator started."""
        return self._events_published

    def vehicle_count(self) -> int:
        """Number of vehicles currently in the in-memory map."""
        return len(self._vehicle_map)

    def set_vehicle_map(self, vehicles: Mapping[str, VehicleInfo]) -> None:
        """Replace the in-memory vehicle map.

        Called by the periodic refresh (external to this class). Replacing
        the whole mapping atomically lets callers build a new snapshot
        without mutating a dict that handle_position might be iterating —
        though in a single-event-loop model that isn't a real risk; the
        method exists for clarity.
        """
        self._vehicle_map = dict(vehicles)

    async def handle_position(self, position: PositionEvent) -> OccupancyEvent | None:
        """Run the detection loop for one position event.

        Returns the OccupancyEvent that was published, or None if no
        arrival fired or the event was skipped (unknown vehicle, missing
        route, transient failure, etc.).
        """

        # 1. Route lookup
        info = self._vehicle_map.get(position.vehicle_id)
        if info is None or info.route_id is None:
            logger.debug("Vehicle %s unknown; skipping position", position.vehicle_id)
            return None

        # 2. Route stops (cached)
        try:
            stops = await self._route_cache.get_route_stops(
                info.route_id, self._service_token
            )
        except Exception:
            logger.exception("Route fetch failed for %s", info.route_id)
            return None
        if len(stops) < 2:
            return None

        # 3. Per-vehicle state: lazy seeding, preserve sequence on route change
        seed: VehicleSeed | None = None
        if not self._state_store.has(position.vehicle_id):
            try:
                seq = await self._sequence_client.fetch_latest_sequence(
                    position.vehicle_id
                )
            except Exception:
                # Never guess 0 on a transient failure — it could collide
                # with a stored arrival_sequence and produce duplicate
                # idempotency keys (§4).
                logger.exception("Sequence seed failed for %s", position.vehicle_id)
                return None
            seed = VehicleSeed(arrival_sequence=seq, onboard=info.current_occupancy)

        lookup = self._state_store.get_or_create(
            position.vehicle_id, info.route_id, seed
        )
        state = lookup.state
        if lookup.released_ids:
            self._globally_on_board -= set(lookup.released_ids)

        # 4. Detect (pure), then apply
        now_mono = time.monotonic()
        arrival = detect_arrival(position, stops, state, now_mono, self._settings)
        published: OccupancyEvent | None = None

        if arrival is not None:
            state.arrival_sequence += 1
            state.last_stop_id = arrival.stop_id
            state.last_arrival_ts = now_mono
            state.armed = False

            rng = make_rng(position.vehicle_id, state.arrival_sequence)
            result = simulate_passengers(
                state=state,
                current_sequence=arrival.sequence,
                stops=stops,
                seating_capacity=info.seating_capacity,
                passenger_pool=self._pool_fetcher.cached_ids(),
                excluded_ids=self._globally_on_board,
                params=self._sim_params,
                rng=rng,
            )
            state.passengers = result.passengers
            state.onboard = result.onboard
            state.needs_synthesis = False
            self._globally_on_board -= set(result.alighted_ids)
            self._globally_on_board |= set(result.boarded_ids)

            event = build_occupancy_event(
                vehicle_id=position.vehicle_id,
                tenant_id=position.tenant_id,
                stop_id=arrival.stop_id,
                route_id=info.route_id,
                onboard=result.onboard,
                boardings=result.boardings,
                alightings=result.alightings,
                arrival_sequence=state.arrival_sequence,
                position_timestamp=position.timestamp.isoformat(),
                boarded_passenger_ids=result.boarded_ids,
                alighted_passenger_ids=result.alighted_ids,
                revenue_delta=result.revenue_delta,
            )
            self._publisher.publish(
                topic=f"gps/{position.tenant_id}/{position.vehicle_id}/occupancy",
                payload=event.model_dump(),
                qos=1,
            )
            self._events_published += 1
            published = event

        # 5. Re-arm + update observations
        self._re_arm_if_far(position, stops, state)
        state.last_lat = position.lat
        state.last_lng = position.lng
        state.last_speed = position.speed
        state.last_position_ts = position.timestamp

        return published

    def release_vehicle(self, vehicle_id: str) -> list[str]:
        """Drop per-vehicle state and release its real passenger IDs.

        Called by the periodic refresh when a vehicle leaves the map.
        Returns the released real IDs; they are already removed from the
        global set.
        """
        released = self._state_store.remove(vehicle_id)
        self._globally_on_board -= set(released)
        return released

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _re_arm_if_far(
        self,
        position: PositionEvent,
        stops: list[RouteStop],
        state: VehicleArrivalState,
    ) -> None:
        """Set state.armed = True when the bus is > radius from the last stop.

        No-op when the bus was never armed (fresh vehicle) or when the
        last stop can't be found (shouldn't happen — the state was
        populated from this stops list — but defensive).
        """

        if state.last_stop_id is None or state.armed:
            return
        last_stop = next((s for s in stops if s.stop_id == state.last_stop_id), None)
        if last_stop is None:
            return
        distance_m = haversine_distance(
            position.lat,
            position.lng,
            last_stop.latitude,
            last_stop.longitude,
        )
        if distance_m > self._settings.STOP_ARRIVAL_RADIUS_M:
            state.armed = True
