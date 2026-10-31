from __future__ import annotations

from datetime import datetime, timezone


from passenger_service.config import PassengerServiceSettings
from passenger_service.detection.detector import detect_arrival
from passenger_service.detection.state import VehicleArrivalState
from passenger_service.models.position import PositionEvent
from passenger_service.models.route_stop import RouteStop


# Settings with detection constants at their defaults:
# STOP_ARRIVAL_RADIUS_M=30.0, STOP_SPEED_THRESHOLD_KMH=5.0,
# STOP_COOLDOWN_SECONDS=60.0 — matching design §3.
_SETTINGS = PassengerServiceSettings()


def _stop(stop_id: str, sequence: int, lat: float, lng: float) -> RouteStop:
    return RouteStop(stop_id=stop_id, latitude=lat, longitude=lng, sequence=sequence)


def _position(
    lat: float,
    lng: float,
    speed: float = 0.0,
    vehicle_id: str = "veh-1",
    tenant_id: str = "ten-1",
) -> PositionEvent:
    return PositionEvent(
        vehicle_id=vehicle_id,
        tenant_id=tenant_id,
        lat=lat,
        lng=lng,
        speed=speed,
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


# ---------------------------------------------------------------------------
# Near + slow → returns the arriving RouteStop
# ---------------------------------------------------------------------------


def test_near_and_slow_returns_stop() -> None:
    stops = [_stop("stp-a", 0, 0.0, 0.0)]
    state = VehicleArrivalState(route_id="rt-1")
    arrival = detect_arrival(
        _position(0.0, 0.0, speed=2.0),
        stops,
        state,
        now_mono=1000.0,
        settings=_SETTINGS,
    )
    assert arrival is not None
    assert arrival.stop_id == "stp-a"


def test_at_radius_boundary_fires() -> None:
    # ~29.9m north of (0, 0): 29.9 / 111194.93 ≈ 0.000268905 degrees lat.
    # Just inside STOP_ARRIVAL_RADIUS_M; asserts the (<=) boundary is inclusive.
    stops = [_stop("stp-a", 0, 0.0, 0.0)]
    state = VehicleArrivalState(route_id="rt-1")
    arrival = detect_arrival(
        _position(0.000268905, 0.0, speed=2.0),
        stops,
        state,
        now_mono=1000.0,
        settings=_SETTINGS,
    )
    assert arrival is not None
    assert arrival.stop_id == "stp-a"


def test_speed_at_threshold_fires() -> None:
    # speed == STOP_SPEED_THRESHOLD_KMH (<=) fires
    stops = [_stop("stp-a", 0, 0.0, 0.0)]
    state = VehicleArrivalState(route_id="rt-1")
    arrival = detect_arrival(
        _position(0.0, 0.0, speed=5.0),
        stops,
        state,
        now_mono=1000.0,
        settings=_SETTINGS,
    )
    assert arrival is not None


# ---------------------------------------------------------------------------
# Near + fast → None
# ---------------------------------------------------------------------------


def test_near_but_fast_returns_none() -> None:
    stops = [_stop("stp-a", 0, 0.0, 0.0)]
    state = VehicleArrivalState(route_id="rt-1")
    arrival = detect_arrival(
        _position(0.0, 0.0, speed=40.0),
        stops,
        state,
        now_mono=1000.0,
        settings=_SETTINGS,
    )
    assert arrival is None


# ---------------------------------------------------------------------------
# Far + slow → None
# ---------------------------------------------------------------------------


def test_far_but_slow_returns_none() -> None:
    stops = [_stop("stp-a", 0, 0.0, 0.0)]
    state = VehicleArrivalState(route_id="rt-1")
    # 1km north: far beyond radius
    arrival = detect_arrival(
        _position(0.009, 0.0, speed=2.0),
        stops,
        state,
        now_mono=1000.0,
        settings=_SETTINGS,
    )
    assert arrival is None


# ---------------------------------------------------------------------------
# Cooldown
# ---------------------------------------------------------------------------


def test_same_stop_within_cooldown_returns_none() -> None:
    stops = [_stop("stp-a", 0, 0.0, 0.0)]
    state = VehicleArrivalState(route_id="rt-1")
    state.last_stop_id = "stp-a"
    state.last_arrival_ts = 1000.0
    state.armed = True  # must not matter; cooldown alone suppresses

    # 30 seconds later — inside 60s cooldown
    arrival = detect_arrival(
        _position(0.0, 0.0, speed=2.0),
        stops,
        state,
        now_mono=1030.0,
        settings=_SETTINGS,
    )
    assert arrival is None


def test_same_stop_after_cooldown_fires() -> None:
    stops = [_stop("stp-a", 0, 0.0, 0.0)]
    state = VehicleArrivalState(route_id="rt-1")
    state.last_stop_id = "stp-a"
    state.last_arrival_ts = 1000.0
    state.armed = True

    arrival = detect_arrival(
        _position(0.0, 0.0, speed=2.0),
        stops,
        state,
        now_mono=1100.0,  # 100s > 60s cooldown
        settings=_SETTINGS,
    )
    assert arrival is not None
    assert arrival.stop_id == "stp-a"


# ---------------------------------------------------------------------------
# Re-arm
# ---------------------------------------------------------------------------


def test_same_stop_with_armed_false_returns_none_even_after_cooldown() -> None:
    """Re-arm guard alone suppresses; cooldown having elapsed doesn't help."""
    stops = [_stop("stp-a", 0, 0.0, 0.0)]
    state = VehicleArrivalState(route_id="rt-1")
    state.last_stop_id = "stp-a"
    state.last_arrival_ts = 1000.0
    state.armed = False

    arrival = detect_arrival(
        _position(0.0, 0.0, speed=2.0),
        stops,
        state,
        now_mono=1200.0,  # well past cooldown
        settings=_SETTINGS,
    )
    assert arrival is None


# ---------------------------------------------------------------------------
# Different stop — never suppressed by cooldown or armed
# ---------------------------------------------------------------------------


def test_different_stop_fires_even_with_armed_false() -> None:
    stops = [
        _stop("stp-a", 0, 0.0, 0.0),
        _stop("stp-b", 1, 0.0001, 0.0),  # ~11m north of A
    ]
    state = VehicleArrivalState(route_id="rt-1")
    state.last_stop_id = "stp-a"
    state.last_arrival_ts = 1000.0
    state.armed = False

    # Position at stp-b, still inside A's radius. Detection should fire
    # on stp-b (different stop from last_stop_id).
    arrival = detect_arrival(
        _position(0.0001, 0.0, speed=2.0),
        stops,
        state,
        now_mono=1030.0,
        settings=_SETTINGS,
    )
    assert arrival is not None
    assert arrival.stop_id == "stp-b"


def test_different_stop_fires_even_within_cooldown() -> None:
    stops = [
        _stop("stp-a", 0, 0.0, 0.0),
        _stop("stp-b", 1, 0.0001, 0.0),
    ]
    state = VehicleArrivalState(route_id="rt-1")
    state.last_stop_id = "stp-a"
    state.last_arrival_ts = 1000.0
    state.armed = True

    arrival = detect_arrival(
        _position(0.0001, 0.0, speed=2.0),
        stops,
        state,
        now_mono=1030.0,  # within 60s cooldown of stp-a
        settings=_SETTINGS,
    )
    assert arrival is not None
    assert arrival.stop_id == "stp-b"


# ---------------------------------------------------------------------------
# First-match in sequence order (not nearest)
# ---------------------------------------------------------------------------


def test_returns_first_stop_in_sequence_order_not_nearest() -> None:
    """When two stops are both near+slow, return the earlier in sequence
    (design §12)."""
    stops = [
        _stop("stp-a", 0, 0.0, 0.0),
        _stop("stp-b", 1, 0.0001, 0.0),  # ~11m north
    ]
    state = VehicleArrivalState(route_id="rt-1")
    # Position closer to stp-b than to stp-a; still inside both radii.
    arrival = detect_arrival(
        _position(0.00009, 0.0, speed=2.0),
        stops,
        state,
        now_mono=1000.0,
        settings=_SETTINGS,
    )
    assert arrival is not None
    assert arrival.stop_id == "stp-a"  # earlier sequence, even though stp-b is nearer


def test_gapped_sequence_data_uses_sequence_not_array_index() -> None:
    """Route with sequences [0, 1, 3] (a stop was deleted). Detection must
    return the RouteStop whose sequence matches; array indices are 0,1,2.

    Regression guard: if the detector were returning an index, this test
    would need adjustment — it asserts on stop_id, so it catches that.
    """
    stops = [
        _stop("stp-zero", 0, 0.0, 0.0),
        _stop("stp-one", 1, 0.001, 0.0),
        _stop("stp-three", 3, 0.002, 0.0),  # note sequence 3, not 2
    ]
    state = VehicleArrivalState(route_id="rt-1")

    # Position at the third stop's coordinates.
    arrival = detect_arrival(
        _position(0.002, 0.0, speed=2.0),
        stops,
        state,
        now_mono=1000.0,
        settings=_SETTINGS,
    )
    assert arrival is not None
    assert arrival.stop_id == "stp-three"
    assert arrival.sequence == 3


# ---------------------------------------------------------------------------
# Purity — no mutation of state
# ---------------------------------------------------------------------------


def test_state_is_not_mutated() -> None:
    """The detector reads state but does not touch it (§3: pure)."""
    stops = [_stop("stp-a", 0, 0.0, 0.0)]
    state = VehicleArrivalState(route_id="rt-1")
    state.last_stop_id = "stp-x"
    state.last_arrival_ts = 999.0
    state.armed = True
    state.arrival_sequence = 42
    state.onboard = 7
    state.passengers = [{"passenger_id": "pas-1"}]

    snapshot = (
        state.route_id,
        state.last_lat,
        state.last_lng,
        state.last_speed,
        state.last_stop_id,
        state.last_arrival_ts,
        state.armed,
        state.arrival_sequence,
        state.onboard,
        state.needs_synthesis,
        state.last_position_ts,
        list(state.passengers),
        state.current_trip_id,
    )

    detect_arrival(
        _position(0.0, 0.0, speed=2.0),
        stops,
        state,
        now_mono=2000.0,
        settings=_SETTINGS,
    )

    after = (
        state.route_id,
        state.last_lat,
        state.last_lng,
        state.last_speed,
        state.last_stop_id,
        state.last_arrival_ts,
        state.armed,
        state.arrival_sequence,
        state.onboard,
        state.needs_synthesis,
        state.last_position_ts,
        list(state.passengers),
        state.current_trip_id,
    )
    assert snapshot == after


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_empty_stops_returns_none() -> None:
    state = VehicleArrivalState(route_id="rt-1")
    arrival = detect_arrival(
        _position(0.0, 0.0, speed=0.0), [], state, now_mono=1000.0, settings=_SETTINGS
    )
    assert arrival is None


def test_single_stop_route_still_detects() -> None:
    stops = [_stop("stp-only", 0, 0.0, 0.0)]
    state = VehicleArrivalState(route_id="rt-1")
    arrival = detect_arrival(
        _position(0.0, 0.0, speed=0.0),
        stops,
        state,
        now_mono=1000.0,
        settings=_SETTINGS,
    )
    assert arrival is not None
    assert arrival.stop_id == "stp-only"


def test_new_vehicle_no_last_arrival_ts_does_not_hit_cooldown() -> None:
    stops = [_stop("stp-a", 0, 0.0, 0.0)]
    state = VehicleArrivalState(route_id="rt-1")
    # No last_arrival_ts, armed=True default → fires.
    arrival = detect_arrival(
        _position(0.0, 0.0, speed=2.0),
        stops,
        state,
        now_mono=1000.0,
        settings=_SETTINGS,
    )
    assert arrival is not None
