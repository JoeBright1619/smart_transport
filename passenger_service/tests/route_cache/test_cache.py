from __future__ import annotations

import pytest
from aioresponses import aioresponses

from passenger_service.route_cache.cache import RouteCache

BACKEND = "http://backend.test"
ROUTE_ID = "rt-abc"


def _route_payload(stops: list[dict]) -> dict:
    return {"data": {"id": ROUTE_ID, "stops": stops}}


def _stop(stop_id: str, order: int, lat: float = 0.0, lng: float = 0.0) -> dict:
    return {"id": stop_id, "lat": lat, "lng": lng, "order": order}


async def test_fetches_and_maps_order_to_sequence() -> None:
    cache = RouteCache(backend_url=BACKEND)
    try:
        with aioresponses() as m:
            m.get(
                f"{BACKEND}/api/v1/routes/{ROUTE_ID}",
                payload=_route_payload(
                    [
                        _stop("stp-1", order=0, lat=1.5, lng=2.5),
                        _stop("stp-2", order=1, lat=3.5, lng=4.5),
                    ]
                ),
            )

            stops = await cache.get_route_stops(ROUTE_ID, token="tok")
    finally:
        await cache.close()

    assert [s.stop_id for s in stops] == ["stp-1", "stp-2"]
    assert stops[0].sequence == 0
    assert stops[1].sequence == 1
    assert stops[0].latitude == 1.5
    assert stops[0].longitude == 2.5


async def test_cache_hit_avoids_second_http_call() -> None:
    cache = RouteCache(backend_url=BACKEND)
    try:
        with aioresponses() as m:
            m.get(
                f"{BACKEND}/api/v1/routes/{ROUTE_ID}",
                payload=_route_payload([_stop("stp-1", order=0)]),
            )

            first = await cache.get_route_stops(ROUTE_ID, token="tok")
            # No second mock registered: a second HTTP call would raise.
            second = await cache.get_route_stops(ROUTE_ID, token="tok")
    finally:
        await cache.close()

    assert first is second or [s.stop_id for s in first] == [s.stop_id for s in second]
    assert len(first) == 1


async def test_ttl_expiry_triggers_refetch(monkeypatch: pytest.MonkeyPatch) -> None:
    cache = RouteCache(backend_url=BACKEND, ttl=60.0)

    # Controllable clock.
    now = [1000.0]
    monkeypatch.setattr(
        "passenger_service.route_cache.cache.time.monotonic",
        lambda: now[0],
    )

    try:
        with aioresponses() as m:
            url = f"{BACKEND}/api/v1/routes/{ROUTE_ID}"
            m.get(url, payload=_route_payload([_stop("stp-1", order=0)]))
            m.get(url, payload=_route_payload([_stop("stp-2", order=0)]))

            first = await cache.get_route_stops(ROUTE_ID, token="tok")

            # Still within TTL — should be cache hit, not the second mock.
            now[0] += 59.0
            still_cached = await cache.get_route_stops(ROUTE_ID, token="tok")

            # Past TTL — should refetch, consuming the second mock.
            now[0] += 2.0
            refreshed = await cache.get_route_stops(ROUTE_ID, token="tok")
    finally:
        await cache.close()

    assert [s.stop_id for s in first] == ["stp-1"]
    assert [s.stop_id for s in still_cached] == ["stp-1"]
    assert [s.stop_id for s in refreshed] == ["stp-2"]


async def test_missing_stops_field_returns_empty_list() -> None:
    cache = RouteCache(backend_url=BACKEND)
    try:
        with aioresponses() as m:
            m.get(
                f"{BACKEND}/api/v1/routes/{ROUTE_ID}",
                payload={"data": {"id": ROUTE_ID}},  # no "stops"
            )
            stops = await cache.get_route_stops(ROUTE_ID, token="tok")
    finally:
        await cache.close()

    assert stops == []


async def test_null_stops_returns_empty_list() -> None:
    cache = RouteCache(backend_url=BACKEND)
    try:
        with aioresponses() as m:
            m.get(
                f"{BACKEND}/api/v1/routes/{ROUTE_ID}",
                payload={"data": {"id": ROUTE_ID, "stops": None}},
            )
            stops = await cache.get_route_stops(ROUTE_ID, token="tok")
    finally:
        await cache.close()

    assert stops == []


async def test_empty_stops_returns_empty_list() -> None:
    cache = RouteCache(backend_url=BACKEND)
    try:
        with aioresponses() as m:
            m.get(
                f"{BACKEND}/api/v1/routes/{ROUTE_ID}",
                payload=_route_payload([]),
            )
            stops = await cache.get_route_stops(ROUTE_ID, token="tok")
    finally:
        await cache.close()

    assert stops == []


async def test_stops_are_sorted_by_sequence_even_when_response_out_of_order() -> None:
    cache = RouteCache(backend_url=BACKEND)
    try:
        with aioresponses() as m:
            m.get(
                f"{BACKEND}/api/v1/routes/{ROUTE_ID}",
                payload=_route_payload(
                    [
                        _stop("stp-c", order=2),
                        _stop("stp-a", order=0),
                        _stop("stp-b", order=1),
                    ]
                ),
            )
            stops = await cache.get_route_stops(ROUTE_ID, token="tok")
    finally:
        await cache.close()

    assert [s.stop_id for s in stops] == ["stp-a", "stp-b", "stp-c"]
    assert [s.sequence for s in stops] == [0, 1, 2]


async def test_cached_value_is_also_sorted() -> None:
    # Sort lives in _fetch_route_stops, so the cached list (and thus any
    # cache-hit return) is sorted too. Guard against future regressions
    # where sorting might be moved out of the fetch path.
    cache = RouteCache(backend_url=BACKEND)
    try:
        with aioresponses() as m:
            m.get(
                f"{BACKEND}/api/v1/routes/{ROUTE_ID}",
                payload=_route_payload(
                    [
                        _stop("stp-z", order=5),
                        _stop("stp-y", order=3),
                    ]
                ),
            )
            await cache.get_route_stops(ROUTE_ID, token="tok")
            cached = await cache.get_route_stops(ROUTE_ID, token="tok")
    finally:
        await cache.close()

    assert [s.sequence for s in cached] == [3, 5]
