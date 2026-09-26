from unittest.mock import AsyncMock, patch

import pytest

from gps_service.models.gps_data import RouteStop
from gps_service.route_cache.cache import RouteCache


@pytest.mark.asyncio
async def test_fetches_route_on_cache_miss():
    cache = RouteCache(
        backend_url="http://localhost:8000",
        ttl=60,
    )

    stops = [
        RouteStop(
            stop_id="stop-001",
            latitude=-1.9441,
            longitude=30.0585,
            sequence=0,
        )
    ]

    cache._fetch_route_stops = AsyncMock(return_value=stops)

    result = await cache.get_route_stops(
        "route-001",
        "test-token",
    )

    assert result == stops
    cache._fetch_route_stops.assert_awaited_once_with(
        "route-001",
        "test-token",
    )

    await cache.close()


@pytest.mark.asyncio
async def test_returns_cached_route_before_ttl_expires():
    cache = RouteCache(
        backend_url="http://localhost:8000",
        ttl=60,
    )

    stops = [
        RouteStop(
            stop_id="stop-001",
            latitude=-1.9441,
            longitude=30.0585,
            sequence=0,
        )
    ]

    cache._fetch_route_stops = AsyncMock(return_value=stops)

    first = await cache.get_route_stops(
        "route-001",
        "test-token",
    )

    second = await cache.get_route_stops(
        "route-001",
        "test-token",
    )

    assert first == second

    cache._fetch_route_stops.assert_awaited_once()

    await cache.close()


@pytest.mark.asyncio
async def test_refreshes_route_after_ttl_expires():
    cache = RouteCache(
        backend_url="http://localhost:8000",
        ttl=60,
    )

    first_stops = [
        RouteStop(
            stop_id="stop-001",
            latitude=-1.9441,
            longitude=30.0585,
            sequence=0,
        )
    ]

    second_stops = [
        RouteStop(
            stop_id="stop-002",
            latitude=-1.9500,
            longitude=30.0600,
            sequence=0,
        )
    ]

    cache._fetch_route_stops = AsyncMock(side_effect=[first_stops, second_stops])

    with patch(
        "gps_service.route_cache.cache.time.monotonic",
        side_effect=[0, 61, 61],
    ):
        await cache.get_route_stops(
            "route-001",
            "test-token",
        )

        result = await cache.get_route_stops(
            "route-001",
            "test-token",
        )

    assert result == second_stops
    assert cache._fetch_route_stops.await_count == 2

    await cache.close()


@pytest.mark.asyncio
async def test_invalidate_removes_cached_route():
    cache = RouteCache(
        backend_url="http://localhost:8000",
        ttl=60,
    )

    stops = [
        RouteStop(
            stop_id="stop-001",
            latitude=-1.9441,
            longitude=30.0585,
            sequence=0,
        )
    ]

    cache._fetch_route_stops = AsyncMock(return_value=stops)

    await cache.get_route_stops("route-001", "test-token")

    cache.invalidate("route-001")

    await cache.get_route_stops("route-001", "test-token")

    assert cache._fetch_route_stops.await_count == 2

    await cache.close()
