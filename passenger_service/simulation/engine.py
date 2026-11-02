"""Passenger simulation engine (design §7).

Pure function: `simulate_passengers` takes state by argument, reads no
module-level state, and returns a `SimulationResult`. The orchestrator
is the only component that mutates `VehicleArrivalState`, `_globally_on_board`,
or publishes occupancy events.

Every random draw comes from the injected `random.Random`. The caller
constructs it via `make_rng(vehicle_id, arrival_sequence)` so that the
same (vehicle, sequence) always produces the same simulation — critical
because occupancy_events are persisted by arrival_sequence and duplicated
publishes must collapse (§4).
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from typing import AbstractSet, Sequence

from passenger_service.detection.state import VehicleArrivalState
from passenger_service.geo import haversine_distance
from passenger_service.models.route_stop import RouteStop


@dataclass(frozen=True)
class SimulationParams:
    """Simulation knobs, constructed by the orchestrator from settings."""

    crush_capacity_factor: float
    revenue_per_km: float


@dataclass
class SimulationResult:
    """Outcome of one stop's simulation. All lists are freshly allocated."""

    boardings: int
    alightings: int
    onboard: int
    revenue_delta: float
    boarded_ids: list[str]
    alighted_ids: list[str]
    passengers: list[dict]


def make_rng(vehicle_id: str, arrival_sequence: int) -> random.Random:
    """Stable-per-(vehicle, arrival) RNG seed.

    SHA-256 digest, first 8 bytes, big-endian → int. Stable across Python
    versions and processes, so a replayed arrival produces identical draws.
    """

    digest = hashlib.sha256(f"{vehicle_id}:{arrival_sequence}".encode()).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))  # nosec


def simulate_passengers(
    state: VehicleArrivalState,
    current_sequence: int,
    stops: list[RouteStop],
    seating_capacity: int,
    passenger_pool: Sequence[str],
    excluded_ids: AbstractSet[str],
    params: SimulationParams,
    rng: random.Random,
) -> SimulationResult:
    """Simulate boarding and alighting for one stop. Pure.

    RNG consumption order (determinism contract):
      1. Synthesis (randint per synthesised passenger)
      2. Alighting (no RNG — dest_sequence == current_sequence)
      3. Boarding (randint per boarder for dest_pos)
      4. Real-ID sample (rng.sample)
      5. Through-passenger re-boarding (randint per through, last stop only)
    """

    pos = _index_of(stops, current_sequence)

    # 1. Synthesis
    if state.needs_synthesis:
        passengers = _synthesise(state.onboard, pos, stops, rng)
    else:
        passengers = [dict(p) for p in state.passengers]

    # 2. Alighting
    alighted_passengers, remaining, revenue = _alight(
        passengers, current_sequence, stops, params.revenue_per_km
    )
    alightings = len(alighted_passengers)
    alighted_ids = [
        p["passenger_id"] for p in alighted_passengers if p["passenger_id"] is not None
    ]

    # 3. Boarding
    last_pos = len(stops) - 1
    is_last_stop = pos == last_pos
    crush_capacity = int(seating_capacity * params.crush_capacity_factor)
    available_seats = crush_capacity - len(remaining)

    new_boarders: list[dict] = []

    if pos == 0 and len(stops) > 1:
        target = rng.randint(int(seating_capacity * 0.75), int(seating_capacity * 1.10))
        n_boarded = max(0, min(target, available_seats))
        for _ in range(n_boarded):
            dest_pos = rng.randint(1, last_pos)
            new_boarders.append(
                {
                    "origin_sequence": stops[0].sequence,
                    "dest_sequence": stops[dest_pos].sequence,
                    "distance_km": _distance_km(stops, 0, dest_pos),
                    "passenger_id": None,
                }
            )
    elif not is_last_stop and available_seats > 0:
        board_cap = max(1, seating_capacity // 6)
        low = min(board_cap // 2, available_seats)
        high = min(board_cap, available_seats)
        n_boarded = rng.randint(low, high)
        for _ in range(n_boarded):
            dest_pos = rng.randint(pos + 1, last_pos)
            new_boarders.append(
                {
                    "origin_sequence": stops[pos].sequence,
                    "dest_sequence": stops[dest_pos].sequence,
                    "distance_km": _distance_km(stops, pos, dest_pos),
                    "passenger_id": None,
                }
            )

    # 4. Real-ID assignment
    remaining_real_ids = {
        p["passenger_id"] for p in remaining if p["passenger_id"] is not None
    }
    alighted_ids_set = set(alighted_ids)
    available = [
        pid
        for pid in passenger_pool
        if pid not in remaining_real_ids
        and pid not in alighted_ids_set
        and pid not in excluded_ids
    ]
    n_real = min(len(new_boarders), len(available))
    boarded_real_ids = rng.sample(available, n_real) if n_real > 0 else []
    for i, pid in enumerate(boarded_real_ids):
        new_boarders[i]["passenger_id"] = pid

    # 5. Through-passengers at the last stop (len(stops) > 2)
    through_boarders: list[dict] = []
    if is_last_stop and len(stops) > 2:
        k = min(rng.randint(3, 6), alightings)
        for _ in range(k):
            dest_pos = rng.randint(1, last_pos)
            through_boarders.append(
                {
                    "origin_sequence": stops[0].sequence,
                    "dest_sequence": stops[dest_pos].sequence,
                    "distance_km": _distance_km(stops, 0, dest_pos),
                    "passenger_id": None,
                }
            )

    # 6. Assemble result
    passengers_after = remaining + new_boarders + through_boarders

    return SimulationResult(
        boardings=len(new_boarders) + len(through_boarders),
        alightings=alightings,
        onboard=len(passengers_after),
        revenue_delta=revenue,
        boarded_ids=boarded_real_ids,
        alighted_ids=alighted_ids,
        passengers=passengers_after,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _index_of(stops: list[RouteStop], sequence: int) -> int:
    """Return the array position of the stop whose .sequence == sequence.

    Stops are sorted by .sequence (Task 3.1); a linear scan is fine at
    demo scale. Raise if the sequence isn't in the route — the caller
    must pass a sequence that came from this stops list.
    """

    for i, stop in enumerate(stops):
        if stop.sequence == sequence:
            return i
    raise ValueError(f"sequence {sequence!r} not found in route stops")


def _distance_km(stops: list[RouteStop], origin_pos: int, dest_pos: int) -> float:
    """Sum of consecutive haversine legs from origin_pos to dest_pos, in km."""

    total_m = 0.0
    for i in range(origin_pos, dest_pos):
        total_m += haversine_distance(
            stops[i].latitude,
            stops[i].longitude,
            stops[i + 1].latitude,
            stops[i + 1].longitude,
        )
    return total_m / 1000.0


def _synthesise(
    onboard: int, pos: int, stops: list[RouteStop], rng: random.Random
) -> list[dict]:
    """Create `onboard` anonymous records with plausible origins/destinations.

    origin_pos ∈ [0, pos-1] (or 0 at terminus), dest_pos ∈ [max(pos, 1), len-1].
    Samples over array positions, then maps to .sequence — robust to gapped
    sequence data (§7 "Synthesising seeded passengers").
    """

    if onboard <= 0:
        return []

    n_stops = len(stops)
    result: list[dict] = []
    for _ in range(onboard):
        if pos > 0:
            origin_pos = rng.randint(0, pos - 1)
        else:
            origin_pos = 0
        dest_pos = rng.randint(max(pos, 1), n_stops - 1)
        result.append(
            {
                "origin_sequence": stops[origin_pos].sequence,
                "dest_sequence": stops[dest_pos].sequence,
                "distance_km": _distance_km(stops, origin_pos, dest_pos),
                "passenger_id": None,
            }
        )
    return result


def _alight(
    passengers: list[dict],
    current_sequence: int,
    stops: list[RouteStop],
    revenue_per_km: float,
) -> tuple[list[dict], list[dict], float]:
    """Return (alighted, remaining, revenue).

    At the last stop (pos == len(stops)-1 and len(stops) > 2), everyone
    alights. At the last stop with len(stops) <= 2, same but no throughs.
    At other stops, only passengers whose dest_sequence == current_sequence
    alight. Compare by sequence, never by array index.
    """

    last_pos = len(stops) - 1
    # current_sequence maps to a position — caller has already validated.
    # The stop being the "last" is determined by comparing current_sequence
    # against the last stop's sequence, so gaps work.
    is_last_stop = current_sequence == stops[last_pos].sequence

    if is_last_stop:
        # Everyone alights.
        revenue = sum(p["distance_km"] for p in passengers) * revenue_per_km
        return passengers, [], revenue

    alighted = [p for p in passengers if p["dest_sequence"] == current_sequence]
    remaining = [p for p in passengers if p["dest_sequence"] != current_sequence]
    revenue = sum(p["distance_km"] for p in alighted) * revenue_per_km
    return alighted, remaining, revenue
