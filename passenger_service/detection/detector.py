"""Stop-arrival detection.

Pure function per design §3: given a position, the route's stops (sorted
by `sequence`), the current per-vehicle state, the current monotonic
time, and settings, return the arriving stop or None. The caller (the
orchestrator, Task 4.3+) is responsible for:

- computing `now_mono` once per position event and passing it in;
- updating `state.arrival_sequence`, `state.last_stop_id`,
  `state.last_arrival_ts`, and `state.armed` after an arrival fires;
- setting `state.armed = True` when a position more than
  STOP_ARRIVAL_RADIUS_M from the last-arrived stop is observed.

The detector only *reads* `state.armed`.
"""

from __future__ import annotations

from passenger_service.config import PassengerServiceSettings
from passenger_service.geo import haversine_distance
from passenger_service.models.position import PositionEvent
from passenger_service.models.route_stop import RouteStop
from passenger_service.detection.state import VehicleArrivalState


def detect_arrival(
    position: PositionEvent,
    stops: list[RouteStop],
    state: VehicleArrivalState,
    now_mono: float,
    settings: PassengerServiceSettings,
) -> RouteStop | None:
    """Return the arriving RouteStop, or None.

    Iterates `stops` in `sequence` order (guaranteed by the route cache,
    Task 3.1) and returns the **first** stop satisfying all of:

    - distance(position, stop) <= STOP_ARRIVAL_RADIUS_M (metres)
    - position.speed <= STOP_SPEED_THRESHOLD_KMH (km/h)
    - not suppressed by cooldown / re-arm

    Cooldown and re-arm both apply to **same-stop** arrivals only:
    a candidate at a *different* stop from `state.last_stop_id` fires
    regardless of `state.armed` or the cooldown, per §3 ("Arrivals at
    different stops are never suppressed").

    Returning the first match in sequence order (not nearest) is
    deliberate (§12): the bus is travelling in sequence direction, so
    the earliest-sequenced stop at which it's near-and-slow is the
    arrival.
    """

    # Speed gates the whole call — a vehicle driving past at speed is
    # not at a stop, regardless of distance (§3).
    if position.speed > settings.STOP_SPEED_THRESHOLD_KMH:
        return None

    for stop in stops:
        distance_m = haversine_distance(
            position.lat, position.lng, stop.latitude, stop.longitude
        )
        if distance_m > settings.STOP_ARRIVAL_RADIUS_M:
            continue

        # Both suppression paths are same-stop only. A different stop
        # fires even if armed is False or the cooldown is active.
        if state.last_stop_id == stop.stop_id:
            if not state.armed:
                continue
            if (
                state.last_arrival_ts is not None
                and now_mono - state.last_arrival_ts < settings.STOP_COOLDOWN_SECONDS
            ):
                continue

        return stop

    return None
