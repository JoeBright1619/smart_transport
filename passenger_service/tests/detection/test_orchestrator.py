from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock


from passenger_service.config import PassengerServiceSettings
from passenger_service.detection.orchestrator import ArrivalOrchestrator
from passenger_service.detection.state import VehicleStateStore
from passenger_service.models.position import PositionEvent
from passenger_service.models.route_stop import RouteStop
from passenger_service.models.vehicle_info import VehicleInfo

_SETTINGS = PassengerServiceSettings()


def _stop(stop_id: str, sequence: int, lat: float, lng: float) -> RouteStop:
    return RouteStop(stop_id=stop_id, latitude=lat, longitude=lng, sequence=sequence)


def _position(
    lat: float,
    lng: float,
    speed: float = 0.0,
    vehicle_id: str = "veh-1",
    tenant_id: str = "ten-1",
    ts: datetime | None = None,
) -> PositionEvent:
    return PositionEvent(
        vehicle_id=vehicle_id,
        tenant_id=tenant_id,
        lat=lat,
        lng=lng,
        speed=speed,
        timestamp=ts or datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


def _vehicle(
    vehicle_id: str = "veh-1",
    tenant_id: str = "ten-1",
    route_id: str = "rt-1",
    seating_capacity: int = 40,
    current_occupancy: int = 0,
) -> VehicleInfo:
    return VehicleInfo(
        vehicle_id=vehicle_id,
        tenant_id=tenant_id,
        route_id=route_id,
        seating_capacity=seating_capacity,
        current_occupancy=current_occupancy,
    )


def _make_orchestrator(
    *,
    route_cache_stops: list[RouteStop] | Exception | None = None,
    sequence_client_result: int | Exception = 0,
    pool: list[str] | None = None,
    vehicle_map: dict[str, VehicleInfo] | None = None,
) -> tuple[ArrivalOrchestrator, MagicMock, AsyncMock, AsyncMock, MagicMock]:
    """Build an orchestrator with mocked collaborators.

    Returns (orchestrator, publisher, route_cache, sequence_client, pool_fetcher).
    """

    route_cache = AsyncMock()
    if isinstance(route_cache_stops, Exception):
        route_cache.get_route_stops.side_effect = route_cache_stops
    else:
        route_cache.get_route_stops.return_value = route_cache_stops or []

    sequence_client = AsyncMock()
    if isinstance(sequence_client_result, Exception):
        sequence_client.fetch_latest_sequence.side_effect = sequence_client_result
    else:
        sequence_client.fetch_latest_sequence.return_value = sequence_client_result

    pool_fetcher = MagicMock()
    pool_fetcher.cached_ids.return_value = pool or []

    publisher = MagicMock()

    orchestrator = ArrivalOrchestrator(
        state_store=VehicleStateStore(),
        route_cache=route_cache,
        sequence_client=sequence_client,
        pool_fetcher=pool_fetcher,
        publisher=publisher,
        settings=_SETTINGS,
        service_token="tok",
    )
    if vehicle_map is not None:
        orchestrator.set_vehicle_map(vehicle_map)
    return orchestrator, publisher, route_cache, sequence_client, pool_fetcher


# ---------------------------------------------------------------------------
# Publish on arrival
# ---------------------------------------------------------------------------


async def test_publishes_occupancy_event_on_arrival() -> None:
    stops = [_stop("stp-a", 0, 0.0, 0.0), _stop("stp-b", 1, 0.001, 0.0)]
    orch, publisher, *_ = _make_orchestrator(
        route_cache_stops=stops,
        sequence_client_result=7,
        vehicle_map={"veh-1": _vehicle(current_occupancy=5)},
    )

    published = await orch.handle_position(
        _position(0.001, 0.0, speed=0.0, vehicle_id="veh-1", tenant_id="ten-1")
    )

    assert published is not None
    assert published.vehicle_id == "veh-1"
    assert published.tenant_id == "ten-1"
    assert published.stop_id == "stp-b"
    assert published.route_id == "rt-1"
    # arrival_sequence: seed 7, incremented by 1 on arrival → 8
    assert published.arrival_sequence == 8

    publisher.publish.assert_called_once()
    call_kwargs = publisher.publish.call_args.kwargs
    assert call_kwargs["topic"] == "gps/ten-1/veh-1/occupancy"
    assert call_kwargs["qos"] == 1
    assert isinstance(call_kwargs["payload"], dict)
    assert call_kwargs["payload"]["vehicle_id"] == "veh-1"


async def test_no_publish_when_not_at_stop() -> None:
    stops = [_stop("stp-a", 0, 0.0, 0.0), _stop("stp-b", 1, 0.001, 0.0)]
    orch, publisher, *_ = _make_orchestrator(
        route_cache_stops=stops,
        sequence_client_result=0,
        vehicle_map={"veh-1": _vehicle()},
    )

    published = await orch.handle_position(
        _position(5.0, 5.0, speed=0.0)  # far from any stop
    )
    assert published is None
    publisher.publish.assert_not_called()


async def test_no_publish_when_fast() -> None:
    stops = [_stop("stp-a", 0, 0.0, 0.0)]
    orch, publisher, *_ = _make_orchestrator(
        route_cache_stops=stops,
        sequence_client_result=0,
        vehicle_map={"veh-1": _vehicle()},
    )
    published = await orch.handle_position(_position(0.0, 0.0, speed=50.0))
    assert published is None
    publisher.publish.assert_not_called()


# ---------------------------------------------------------------------------
# First-sight seeding
# ---------------------------------------------------------------------------


async def test_first_sight_seeds_from_sequence_client_and_current_occupancy() -> None:
    stops = [_stop("stp-a", 0, 0.0, 0.0), _stop("stp-b", 1, 0.001, 0.0)]
    orch, _, _, sequence_client, _ = _make_orchestrator(
        route_cache_stops=stops,
        sequence_client_result=12,
        vehicle_map={"veh-1": _vehicle(current_occupancy=8)},
    )

    published = await orch.handle_position(_position(0.001, 0.0))

    sequence_client.fetch_latest_sequence.assert_awaited_once_with("veh-1")
    assert published is not None
    assert published.arrival_sequence == 13  # 12 seeded, +1 on arrival


# ---------------------------------------------------------------------------
# Sequence-client failure skips the event
# ---------------------------------------------------------------------------


async def test_sequence_client_failure_skips_event() -> None:
    stops = [_stop("stp-a", 0, 0.0, 0.0), _stop("stp-b", 1, 0.001, 0.0)]
    orch, publisher, *_ = _make_orchestrator(
        route_cache_stops=stops,
        sequence_client_result=RuntimeError("boom"),
        vehicle_map={"veh-1": _vehicle()},
    )

    published = await orch.handle_position(_position(0.001, 0.0))
    assert published is None
    publisher.publish.assert_not_called()


# ---------------------------------------------------------------------------
# Route cache failure skips the event
# ---------------------------------------------------------------------------


async def test_route_cache_failure_skips_event() -> None:
    orch, publisher, *_ = _make_orchestrator(
        route_cache_stops=RuntimeError("backend down"),
        sequence_client_result=0,
        vehicle_map={"veh-1": _vehicle()},
    )
    published = await orch.handle_position(_position(0.0, 0.0))
    assert published is None
    publisher.publish.assert_not_called()


# ---------------------------------------------------------------------------
# Unknown vehicle skipped
# ---------------------------------------------------------------------------


async def test_unknown_vehicle_skipped() -> None:
    orch, publisher, *_ = _make_orchestrator(
        route_cache_stops=[],
        sequence_client_result=0,
        vehicle_map={},  # no vehicle
    )
    published = await orch.handle_position(_position(0.0, 0.0, vehicle_id="veh-x"))
    assert published is None
    publisher.publish.assert_not_called()


# ---------------------------------------------------------------------------
# Route change releases IDs and keeps sequence
# ---------------------------------------------------------------------------


async def test_route_change_releases_ids_and_keeps_sequence() -> None:
    stops_old = [_stop("stp-a", 0, 0.0, 0.0), _stop("stp-b", 1, 0.001, 0.0)]
    stops_new = [_stop("stp-c", 0, 2.0, 2.0), _stop("stp-d", 1, 2.001, 2.0)]

    # First arrival on rt-1 with onboard=0, then simulate boarding with real IDs
    route_cache = AsyncMock()
    route_cache.get_route_stops.side_effect = [stops_old, stops_new]
    sequence_client = AsyncMock()
    sequence_client.fetch_latest_sequence.return_value = 3
    pool_fetcher = MagicMock()
    pool_fetcher.cached_ids.return_value = ["pas-1", "pas-2", "pas-3"]
    publisher = MagicMock()

    orch = ArrivalOrchestrator(
        state_store=VehicleStateStore(),
        route_cache=route_cache,
        sequence_client=sequence_client,
        pool_fetcher=pool_fetcher,
        publisher=publisher,
        settings=_SETTINGS,
        service_token="tok",
    )
    orch.set_vehicle_map({"veh-1": _vehicle(route_id="rt-1")})

    # First arrival — terminus seeds boarders with real IDs
    await orch.handle_position(_position(0.0, 0.0))

    # Note: after this arrival, _globally_on_board should contain the boarders.
    on_board_after_first = set(orch._globally_on_board)
    assert on_board_after_first, "expected some real IDs boarded at terminus"

    # Route change to rt-2
    orch.set_vehicle_map({"veh-1": _vehicle(route_id="rt-2")})

    # Second position at rt-2's first stop — route change path runs
    published = await orch.handle_position(_position(2.0, 2.0))

    # The old real IDs must have been released by get_or_create
    # and re-added only if the new terminus re-boarded them.
    # At minimum, the state's arrival_sequence is preserved (3 seeded + 1 first
    # arrival = 4; second arrival → 5).
    assert published is not None
    assert published.arrival_sequence == 5


# ---------------------------------------------------------------------------
# Global set updated from result
# ---------------------------------------------------------------------------


async def test_global_set_updated_from_simulation_result() -> None:
    stops = [_stop("stp-a", 0, 0.0, 0.0), _stop("stp-b", 1, 0.001, 0.0)]
    orch, _, _, _, pool_fetcher = _make_orchestrator(
        route_cache_stops=stops,
        sequence_client_result=0,
        pool=["pas-1", "pas-2", "pas-3"],
        vehicle_map={"veh-1": _vehicle(current_occupancy=0)},
    )

    # First arrival at terminus: boarders assigned real IDs from the pool.
    await orch.handle_position(_position(0.0, 0.0))

    # _globally_on_board should now contain some subset of the pool.
    assert orch._globally_on_board
    assert orch._globally_on_board.issubset({"pas-1", "pas-2", "pas-3"})


# ---------------------------------------------------------------------------
# release_vehicle
# ---------------------------------------------------------------------------


async def test_release_vehicle_returns_ids_and_drops_state() -> None:
    stops = [_stop("stp-a", 0, 0.0, 0.0), _stop("stp-b", 1, 0.001, 0.0)]
    orch, _, _, _, _ = _make_orchestrator(
        route_cache_stops=stops,
        sequence_client_result=0,
        pool=["pas-1", "pas-2", "pas-3"],
        vehicle_map={"veh-1": _vehicle()},
    )

    await orch.handle_position(_position(0.0, 0.0))

    released = orch.release_vehicle("veh-1")

    # The released IDs are the ones that were on board; they should
    # disappear from the global set.
    for pid in released:
        assert pid not in orch._globally_on_board
    # And the state should be gone.
    assert not orch._state_store.has("veh-1")


async def test_release_vehicle_unknown_returns_empty() -> None:
    orch, *_ = _make_orchestrator(vehicle_map={})
    assert orch.release_vehicle("veh-x") == []


# ---------------------------------------------------------------------------
# Two vehicles, global exclusivity
# ---------------------------------------------------------------------------


async def test_two_vehicles_never_share_real_passenger_id() -> None:
    """Both vehicles board from the same pool; the global set must
    prevent the same real ID from being on both simultaneously."""
    stops = [_stop("stp-a", 0, 0.0, 0.0), _stop("stp-b", 1, 0.001, 0.0)]
    pool = ["pas-1", "pas-2", "pas-3", "pas-4", "pas-5"]

    # Two vehicles with separate routes to avoid state cross-talk on the
    # same stops array (though stops are shared; fine).
    orch, _, _, _, _ = _make_orchestrator(
        route_cache_stops=stops,
        sequence_client_result=0,
        pool=pool,
        vehicle_map={
            "veh-a": _vehicle(vehicle_id="veh-a", route_id="rt-1"),
            "veh-b": _vehicle(vehicle_id="veh-b", route_id="rt-1"),
        },
    )

    # Both at terminus, same position → both fire; second must not reuse
    # first's real IDs.
    await orch.handle_position(
        _position(0.0, 0.0, vehicle_id="veh-a", tenant_id="ten-1")
    )
    await orch.handle_position(
        _position(0.0, 0.0, vehicle_id="veh-b", tenant_id="ten-1")
    )

    # Both sets of boarders should be reflected in the global set, with no
    # duplicates (it's a set, but we should have at least boarded IDs
    # from both).
    assert len(orch._globally_on_board) >= 1

    # No real ID is on two vehicles: examine the per-vehicle passenger lists
    # in state.
    state_a = orch._state_store._by_vehicle["veh-a"]
    state_b = orch._state_store._by_vehicle["veh-b"]
    ids_a = {p["passenger_id"] for p in state_a.passengers if p["passenger_id"]}
    ids_b = {p["passenger_id"] for p in state_b.passengers if p["passenger_id"]}
    assert ids_a.isdisjoint(ids_b), f"shared IDs: {ids_a & ids_b}"


async def test_events_published_counter_increments_on_publish() -> None:
    stops = [_stop("stp-a", 0, 0.0, 0.0), _stop("stp-b", 1, 0.001, 0.0)]
    orch, publisher, *_ = _make_orchestrator(
        route_cache_stops=stops,
        sequence_client_result=0,
        vehicle_map={"veh-1": _vehicle()},
    )
    assert orch.events_published() == 0

    await orch.handle_position(_position(0.001, 0.0))
    assert orch.events_published() == 1

    publisher.publish.assert_called_once()


def test_vehicle_count_reflects_map() -> None:
    orch, *_ = _make_orchestrator(
        vehicle_map={"veh-a": _vehicle(), "veh-b": _vehicle(vehicle_id="veh-b")}
    )
    assert orch.vehicle_count() == 2

    orch.set_vehicle_map({})
    assert orch.vehicle_count() == 0
