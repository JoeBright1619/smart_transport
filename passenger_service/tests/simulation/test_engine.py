from __future__ import annotations


import pytest

from passenger_service.detection.state import VehicleArrivalState
from passenger_service.models.route_stop import RouteStop
from passenger_service.simulation.engine import (
    SimulationParams,
    make_rng,
    simulate_passengers,
)


_PARAMS = SimulationParams(crush_capacity_factor=1.15, revenue_per_km=60.0)


def _stops(*coords: tuple[float, float]) -> list[RouteStop]:
    """Build a route from (lat, lng) tuples; sequence = array index."""
    return [
        RouteStop(stop_id=f"stp-{i}", latitude=lat, longitude=lng, sequence=i)
        for i, (lat, lng) in enumerate(coords)
    ]


def _gapped_stops(*coords_with_seq: tuple[int, float, float]) -> list[RouteStop]:
    """Build a route from (sequence, lat, lng) tuples (gapped sequences allowed)."""
    return [
        RouteStop(stop_id=f"stp-{seq}", latitude=lat, longitude=lng, sequence=seq)
        for seq, lat, lng in coords_with_seq
    ]


def _pax(pid: str | None, origin: int, dest: int, distance_km: float = 1.0) -> dict:
    return {
        "origin_sequence": origin,
        "dest_sequence": dest,
        "distance_km": distance_km,
        "passenger_id": pid,
    }


# ---------------------------------------------------------------------------
# make_rng determinism
# ---------------------------------------------------------------------------


def test_make_rng_is_deterministic() -> None:
    a = make_rng("veh-1", 7)
    b = make_rng("veh-1", 7)
    assert [a.random() for _ in range(5)] == [b.random() for _ in range(5)]


def test_make_rng_differs_per_vehicle_and_sequence() -> None:
    base = [make_rng("veh-1", 1).random() for _ in range(3)]
    other_veh = [make_rng("veh-2", 1).random() for _ in range(3)]
    other_seq = [make_rng("veh-1", 2).random() for _ in range(3)]
    assert base != other_veh
    assert base != other_seq


# ---------------------------------------------------------------------------
# Terminus
# ---------------------------------------------------------------------------


def test_terminus_loads_within_range() -> None:
    stops = _stops((0, 0), (0.001, 0), (0.002, 0), (0.003, 0))
    state = VehicleArrivalState(route_id="rt-1")  # empty bus
    rng = make_rng("veh-1", 1)

    result = simulate_passengers(
        state=state,
        current_sequence=0,
        stops=stops,
        seating_capacity=40,
        passenger_pool=[],
        excluded_ids=set(),
        params=_PARAMS,
        rng=rng,
    )

    # target ∈ [30, 44]; crush_capacity = 46; bus empty
    assert 30 <= result.boardings <= 44
    assert result.onboard == result.boardings
    for p in result.passengers:
        # Every boarder's dest must be a later stop (sequence > 0)
        assert p["dest_sequence"] > 0
        assert p["origin_sequence"] == 0


def test_terminus_capped_by_crush_capacity() -> None:
    stops = _stops((0, 0), (0.001, 0), (0.002, 0))
    state = VehicleArrivalState(route_id="rt-1")
    rng = make_rng("veh-1", 3)

    result = simulate_passengers(
        state=state,
        current_sequence=0,
        stops=stops,
        seating_capacity=40,
        passenger_pool=[],
        excluded_ids=set(),
        params=_PARAMS,
        rng=rng,
    )
    assert result.onboard <= int(40 * 1.15)


# ---------------------------------------------------------------------------
# Mid-route
# ---------------------------------------------------------------------------


def test_midroute_respects_board_cap() -> None:
    stops = _stops((0, 0), (0.001, 0), (0.002, 0), (0.003, 0))
    state = VehicleArrivalState(route_id="rt-1")
    rng = make_rng("veh-1", 5)

    result = simulate_passengers(
        state=state,
        current_sequence=1,
        stops=stops,
        seating_capacity=40,
        passenger_pool=[],
        excluded_ids=set(),
        params=_PARAMS,
        rng=rng,
    )
    # board_cap = max(1, 40 // 6) = 6
    assert 0 <= result.boardings <= 6


def test_midroute_respects_available_seats() -> None:
    stops = _stops((0, 0), (0.001, 0), (0.002, 0), (0.003, 0))
    # Fill the bus to crush capacity
    crush = int(40 * 1.15)
    state = VehicleArrivalState(
        route_id="rt-1",
        onboard=crush,
        passengers=[_pax(None, 0, 3) for _ in range(crush)],
    )
    rng = make_rng("veh-1", 9)

    result = simulate_passengers(
        state=state,
        current_sequence=1,
        stops=stops,
        seating_capacity=40,
        passenger_pool=[],
        excluded_ids=set(),
        params=_PARAMS,
        rng=rng,
    )
    assert result.boardings == 0
    assert result.onboard == crush


# ---------------------------------------------------------------------------
# Last stop
# ---------------------------------------------------------------------------


def test_last_stop_all_alight_and_through_reboard() -> None:
    stops = _stops((0, 0), (0.001, 0), (0.002, 0), (0.003, 0))
    state = VehicleArrivalState(
        route_id="rt-1",
        onboard=3,
        passengers=[
            _pax("pas-a", 0, 3, distance_km=1.0),
            _pax("pas-b", 1, 3, distance_km=0.5),
            _pax(None, 0, 3, distance_km=1.0),
        ],
    )
    rng = make_rng("veh-1", 10)

    result = simulate_passengers(
        state=state,
        current_sequence=3,
        stops=stops,
        seating_capacity=40,
        passenger_pool=[],
        excluded_ids=set(),
        params=_PARAMS,
        rng=rng,
    )

    assert result.alightings == 3
    assert sorted(result.alighted_ids) == ["pas-a", "pas-b"]
    # Through-passengers: randint(3, 6) capped by alightings=3 → 3
    assert 3 <= result.boardings <= 6
    assert result.onboard == result.boardings
    assert all(p["passenger_id"] is None for p in result.passengers)
    assert all(p["origin_sequence"] == 0 for p in result.passengers)


def test_last_stop_two_stops_no_through() -> None:
    stops = _stops((0, 0), (0.001, 0))
    state = VehicleArrivalState(
        route_id="rt-1",
        onboard=2,
        passengers=[
            _pax("pas-a", 0, 1),
            _pax(None, 0, 1),
        ],
    )
    rng = make_rng("veh-1", 11)

    result = simulate_passengers(
        state=state,
        current_sequence=1,
        stops=stops,
        seating_capacity=40,
        passenger_pool=[],
        excluded_ids=set(),
        params=_PARAMS,
        rng=rng,
    )
    assert result.alightings == 2
    assert result.boardings == 0
    assert result.onboard == 0


# ---------------------------------------------------------------------------
# Synthesis
# ---------------------------------------------------------------------------


def test_synthesis_matches_onboard_count() -> None:
    stops = _stops((0, 0), (0.001, 0), (0.002, 0), (0.003, 0))
    state = VehicleArrivalState(
        route_id="rt-1",
        onboard=5,
        needs_synthesis=True,
        passengers=[],
    )
    rng = make_rng("veh-1", 20)

    result = simulate_passengers(
        state=state,
        current_sequence=2,
        stops=stops,
        seating_capacity=40,
        passenger_pool=[],
        excluded_ids=set(),
        params=_PARAMS,
        rng=rng,
    )
    # 5 synthesised; any with dest_sequence==2 (current) alight immediately.
    # Sum of alighted + remaining == 5 before new boarders.
    assert result.alightings + (result.onboard - result.boardings) == 5


def test_synthesis_nobody_dest_behind_bus() -> None:
    stops = _stops((0, 0), (0.001, 0), (0.002, 0), (0.003, 0))
    state = VehicleArrivalState(
        route_id="rt-1", onboard=20, needs_synthesis=True, passengers=[]
    )
    rng = make_rng("veh-1", 21)
    result = simulate_passengers(
        state=state,
        current_sequence=2,
        stops=stops,
        seating_capacity=100,
        passenger_pool=[],
        excluded_ids=set(),
        params=_PARAMS,
        rng=rng,
    )
    # No remaining passenger may have dest_sequence < 2 (behind the bus).
    for p in result.passengers:
        assert p["dest_sequence"] >= 2


# ---------------------------------------------------------------------------
# Real-ID assignment
# ---------------------------------------------------------------------------


def test_real_ids_respect_excluded_and_remaining_and_alighted() -> None:
    stops = _stops((0, 0), (0.001, 0), (0.002, 0), (0.003, 0))
    # One existing passenger with real ID "pas-already", one with real ID
    # "pas-alights" alighting at stop 1.
    state = VehicleArrivalState(
        route_id="rt-1",
        onboard=2,
        passengers=[
            _pax("pas-already", 0, 3, distance_km=1.5),
            _pax("pas-alights", 0, 1, distance_km=0.5),
        ],
    )
    rng = make_rng("veh-1", 30)
    result = simulate_passengers(
        state=state,
        current_sequence=1,
        stops=stops,
        seating_capacity=100,
        passenger_pool=["pas-already", "pas-alights", "pas-excluded", "pas-ok"],
        excluded_ids={"pas-excluded"},
        params=_PARAMS,
        rng=rng,
    )
    assert "pas-already" not in result.boarded_ids
    assert "pas-alights" not in result.boarded_ids
    assert "pas-excluded" not in result.boarded_ids


# ---------------------------------------------------------------------------
# Revenue
# ---------------------------------------------------------------------------


def test_revenue_is_sum_of_alighter_distances_times_rate() -> None:
    stops = _stops((0, 0), (0.001, 0), (0.002, 0), (0.003, 0))
    state = VehicleArrivalState(
        route_id="rt-1",
        onboard=3,
        passengers=[
            _pax(None, 0, 1, distance_km=2.0),
            _pax(None, 0, 1, distance_km=3.0),
            _pax(None, 0, 3, distance_km=1.0),  # does not alight yet
        ],
    )
    rng = make_rng("veh-1", 40)
    result = simulate_passengers(
        state=state,
        current_sequence=1,
        stops=stops,
        seating_capacity=40,
        passenger_pool=[],
        excluded_ids=set(),
        params=_PARAMS,
        rng=rng,
    )
    assert result.alightings == 2
    assert result.revenue_delta == pytest.approx((2.0 + 3.0) * 60.0)


# ---------------------------------------------------------------------------
# Determinism / purity / constraints
# ---------------------------------------------------------------------------


def test_determinism_same_seed_same_output() -> None:
    stops = _stops((0, 0), (0.001, 0), (0.002, 0), (0.003, 0))
    state = VehicleArrivalState(
        route_id="rt-1",
        onboard=4,
        passengers=[_pax(None, 0, 3) for _ in range(4)],
    )

    def _run() -> dict:
        rng = make_rng("veh-1", 50)
        r = simulate_passengers(
            state=state,
            current_sequence=1,
            stops=stops,
            seating_capacity=40,
            passenger_pool=["p1", "p2", "p3", "p4", "p5"],
            excluded_ids=set(),
            params=_PARAMS,
            rng=rng,
        )
        return {
            "boardings": r.boardings,
            "alightings": r.alightings,
            "onboard": r.onboard,
            "revenue": r.revenue_delta,
            "boarded_ids": sorted(r.boarded_ids),
            "alighted_ids": sorted(r.alighted_ids),
            "passengers": [
                (p["origin_sequence"], p["dest_sequence"], p["passenger_id"])
                for p in r.passengers
            ],
        }

    assert _run() == _run()


def test_purity_state_not_mutated() -> None:
    stops = _stops((0, 0), (0.001, 0), (0.002, 0), (0.003, 0))
    state = VehicleArrivalState(
        route_id="rt-1",
        onboard=2,
        passengers=[
            _pax("pas-a", 0, 3, distance_km=1.5),
            _pax(None, 0, 3, distance_km=1.5),
        ],
    )
    snapshot = (state.onboard, [dict(p) for p in state.passengers])

    simulate_passengers(
        state=state,
        current_sequence=1,
        stops=stops,
        seating_capacity=40,
        passenger_pool=[],
        excluded_ids=set(),
        params=_PARAMS,
        rng=make_rng("veh-1", 60),
    )

    assert state.onboard == snapshot[0]
    assert state.passengers == snapshot[1]


def test_constraints_alightings_and_onboard_consistent() -> None:
    stops = _stops((0, 0), (0.001, 0), (0.002, 0), (0.003, 0))
    state = VehicleArrivalState(
        route_id="rt-1",
        onboard=5,
        passengers=[
            _pax("pas-a", 0, 1, distance_km=0.5),
            _pax(None, 0, 1, distance_km=0.5),
            _pax(None, 0, 3, distance_km=1.5),
            _pax(None, 0, 3, distance_km=1.5),
            _pax(None, 0, 3, distance_km=1.5),
        ],
    )
    rng = make_rng("veh-1", 70)
    result = simulate_passengers(
        state=state,
        current_sequence=1,
        stops=stops,
        seating_capacity=40,
        passenger_pool=[],
        excluded_ids=set(),
        params=_PARAMS,
        rng=rng,
    )
    assert result.alightings <= 5
    assert result.onboard == len(result.passengers)


# ---------------------------------------------------------------------------
# Gapped sequence data
# ---------------------------------------------------------------------------


def test_gapped_sequence_alight_by_sequence_not_index() -> None:
    """Route with sequences [0, 1, 3]. A passenger with dest_sequence=3
    must alight when current_sequence=3 (last stop), not when array
    index reaches 2."""
    stops = _gapped_stops((0, 0.0, 0.0), (1, 0.001, 0.0), (3, 0.002, 0.0))
    state = VehicleArrivalState(
        route_id="rt-1",
        onboard=2,
        passengers=[
            _pax(None, 0, 3, distance_km=1.5),
            _pax(None, 0, 1, distance_km=0.5),
        ],
    )
    rng = make_rng("veh-1", 80)
    result = simulate_passengers(
        state=state,
        current_sequence=3,
        stops=stops,
        seating_capacity=40,
        passenger_pool=[],
        excluded_ids=set(),
        params=_PARAMS,
        rng=rng,
    )
    # Last stop → everyone alights, through-passengers added (len=3 > 2).
    assert result.alightings == 2
