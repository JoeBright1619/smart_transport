from __future__ import annotations

from passenger_service.detection.state import (
    StateLookup,
    VehicleArrivalState,
    VehicleSeed,
    VehicleStateStore,
)


def _pax(
    passenger_id: str | None, origin_sequence: int = 0, dest_sequence: int = 1
) -> dict:
    """Per-passenger record per design §7."""
    return {
        "origin_sequence": origin_sequence,
        "dest_sequence": dest_sequence,
        "distance_km": 1.5,
        "passenger_id": passenger_id,
    }


# ---------------------------------------------------------------------------
# VehicleArrivalState / VehicleSeed / StateLookup shapes
# ---------------------------------------------------------------------------


def test_state_has_expected_defaults() -> None:
    state = VehicleArrivalState()
    assert state.route_id is None
    assert state.arrival_sequence == 0
    assert state.onboard == 0
    assert state.armed is True
    assert state.needs_synthesis is False
    assert state.last_stop_id is None
    assert state.last_arrival_ts is None
    assert state.last_position_ts is None
    assert state.passengers == []
    assert state.current_trip_id is None


def test_state_has_no_vehicle_id_field() -> None:
    """The store keys by vehicle_id; the state does not carry one (§3)."""
    state = VehicleArrivalState()
    assert not hasattr(state, "vehicle_id")


def test_state_has_no_passenger_pool_field() -> None:
    """The pool is universal/process-wide and passed by argument (§7)."""
    state = VehicleArrivalState()
    assert not hasattr(state, "passenger_pool")


def test_vehicle_seed_defaults() -> None:
    seed = VehicleSeed()
    assert seed.arrival_sequence == 0
    assert seed.onboard == 0


def test_state_lookup_released_ids_default_empty() -> None:
    lookup = StateLookup(state=VehicleArrivalState())
    assert lookup.released_ids == []


# ---------------------------------------------------------------------------
# has / get_or_create — new vehicle
# ---------------------------------------------------------------------------


def test_has_returns_false_for_unknown_vehicle() -> None:
    store = VehicleStateStore()
    assert store.has("veh-x") is False


def test_get_or_create_without_seed_uses_defaults() -> None:
    store = VehicleStateStore()
    lookup = store.get_or_create("veh-1", "rt-1")

    assert isinstance(lookup, StateLookup)
    assert lookup.released_ids == []
    assert lookup.state.route_id == "rt-1"
    assert lookup.state.arrival_sequence == 0
    assert lookup.state.onboard == 0
    assert lookup.state.needs_synthesis is False
    assert lookup.state.armed is True
    assert store.has("veh-1") is True


def test_get_or_create_with_seed_applies_sequence_and_onboard() -> None:
    store = VehicleStateStore()
    lookup = store.get_or_create(
        "veh-1", "rt-1", VehicleSeed(arrival_sequence=42, onboard=10)
    )

    assert lookup.state.arrival_sequence == 42
    assert lookup.state.onboard == 10
    # onboard > 0 on first appearance → synthesis pending
    assert lookup.state.needs_synthesis is True


def test_get_or_create_with_zero_onboard_seed_does_not_need_synthesis() -> None:
    store = VehicleStateStore()
    lookup = store.get_or_create(
        "veh-1", "rt-1", VehicleSeed(arrival_sequence=7, onboard=0)
    )
    assert lookup.state.needs_synthesis is False


# ---------------------------------------------------------------------------
# Persistence across calls / same-route behaviour
# ---------------------------------------------------------------------------


def test_get_or_create_same_route_returns_same_state_object() -> None:
    store = VehicleStateStore()
    first = store.get_or_create("veh-1", "rt-1")
    first.state.arrival_sequence = 5
    first.state.onboard = 3

    second = store.get_or_create("veh-1", "rt-1")

    assert second.state is first.state
    assert second.released_ids == []
    # Fields persisted
    assert second.state.arrival_sequence == 5
    assert second.state.onboard == 3


def test_get_or_create_same_route_ignores_seed() -> None:
    store = VehicleStateStore()
    store.get_or_create("veh-1", "rt-1", VehicleSeed(arrival_sequence=1, onboard=2))

    # Same route; a fresh seed should be ignored.
    second = store.get_or_create(
        "veh-1", "rt-1", VehicleSeed(arrival_sequence=99, onboard=99)
    )
    assert second.state.arrival_sequence == 1
    assert second.state.onboard == 2


# ---------------------------------------------------------------------------
# Route change
# ---------------------------------------------------------------------------


def test_route_change_preserves_sequence_and_onboard() -> None:
    store = VehicleStateStore()
    store.get_or_create("veh-1", "rt-1", VehicleSeed(arrival_sequence=42, onboard=7))

    lookup = store.get_or_create(
        "veh-1", "rt-2", VehicleSeed(arrival_sequence=999, onboard=999)
    )

    # Seed is ignored on route change; existing sequence/onboard preserved.
    assert lookup.state.route_id == "rt-2"
    assert lookup.state.arrival_sequence == 42
    assert lookup.state.onboard == 7


def test_route_change_sets_needs_synthesis_when_onboard_positive() -> None:
    store = VehicleStateStore()
    store.get_or_create("veh-1", "rt-1", VehicleSeed(arrival_sequence=1, onboard=5))
    lookup = store.get_or_create("veh-1", "rt-2")
    assert lookup.state.needs_synthesis is True


def test_route_change_does_not_need_synthesis_when_onboard_zero() -> None:
    store = VehicleStateStore()
    store.get_or_create("veh-1", "rt-1", VehicleSeed(arrival_sequence=1, onboard=0))
    lookup = store.get_or_create("veh-1", "rt-2")
    assert lookup.state.needs_synthesis is False


def test_route_change_clears_observation_fields_and_passengers() -> None:
    store = VehicleStateStore()
    lookup = store.get_or_create("veh-1", "rt-1")
    state = lookup.state
    state.last_stop_id = "stp-9"
    state.last_arrival_ts = 123.4
    state.last_lat = 1.0
    state.last_lng = 2.0
    state.last_speed = 40.0
    from datetime import datetime, timezone

    state.last_position_ts = datetime(2026, 1, 1, tzinfo=timezone.utc)
    state.armed = False
    state.passengers = [_pax("pas-a"), _pax(None)]

    lookup = store.get_or_create("veh-1", "rt-2")
    state = lookup.state

    assert state.last_stop_id is None
    assert state.last_arrival_ts is None
    assert state.last_lat is None
    assert state.last_lng is None
    assert state.last_speed is None
    assert state.last_position_ts is None
    assert state.armed is True
    assert state.passengers == []


def test_route_change_returns_real_ids_only() -> None:
    store = VehicleStateStore()
    lookup = store.get_or_create("veh-1", "rt-1")
    lookup.state.passengers = [
        _pax("pas-real-1"),
        _pax(None),  # anonymous
        _pax("pas-real-2"),
        _pax(""),  # defensive: empty string is treated as anonymous
    ]

    lookup = store.get_or_create("veh-1", "rt-2")

    assert sorted(lookup.released_ids) == ["pas-real-1", "pas-real-2"]


# ---------------------------------------------------------------------------
# remove
# ---------------------------------------------------------------------------


def test_remove_unknown_returns_empty() -> None:
    store = VehicleStateStore()
    assert store.remove("veh-missing") == []
    assert store.has("veh-missing") is False


def test_remove_returns_real_ids_and_drops_state() -> None:
    store = VehicleStateStore()
    lookup = store.get_or_create("veh-1", "rt-1")
    lookup.state.passengers = [_pax("pas-1"), _pax(None), _pax("pas-2")]

    released = store.remove("veh-1")

    assert sorted(released) == ["pas-1", "pas-2"]
    assert store.has("veh-1") is False


def test_remove_then_get_or_create_starts_fresh() -> None:
    store = VehicleStateStore()
    first = store.get_or_create(
        "veh-1", "rt-1", VehicleSeed(arrival_sequence=9, onboard=4)
    )
    first.state.armed = False

    store.remove("veh-1")

    second = store.get_or_create("veh-1", "rt-1")
    assert second.state.arrival_sequence == 0  # fresh state
    assert second.state.onboard == 0
    assert second.state.armed is True
