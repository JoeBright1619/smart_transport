from __future__ import annotations

import time
from dataclasses import dataclass

import aiohttp

from gps_service.models.gps_data import RouteStop


@dataclass
class CachedRoute:
    stops: list[RouteStop]
    expires_at: float


class RouteCache:
    """Cache route stops fetched from the Smart Transport backend."""

    def __init__(
        self,
        backend_url: str,
        ttl: float = 60.0,
    ) -> None:
        self.backend_url = backend_url.rstrip("/")
        self.ttl = ttl

        self._cache: dict[str, CachedRoute] = {}
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()

        return self._session

    async def get_route_stops(
        self,
        route_id: str,
        token: str,
    ) -> list[RouteStop]:
        """Return cached stops or fetch fresh stops when the cache expires."""

        cached = self._cache.get(route_id)

        if cached and cached.expires_at > time.monotonic():
            return cached.stops

        stops = await self._fetch_route_stops(route_id, token)

        self._cache[route_id] = CachedRoute(
            stops=stops,
            expires_at=time.monotonic() + self.ttl,
        )

        return stops

    async def _fetch_route_stops(
        self,
        route_id: str,
        token: str,
    ) -> list[RouteStop]:
        """Fetch route stops from the backend API."""

        session = await self._get_session()

        url = f"{self.backend_url}/routes/{route_id}"

        headers = {
            "Authorization": f"Bearer {token}",
        }

        async with session.get(url, headers=headers) as response:
            response.raise_for_status()
            payload = await response.json()

        route_data = payload["data"]

        return [
            RouteStop(
                stop_id=stop["id"],
                latitude=stop["lat"],
                longitude=stop["lng"],
                sequence=stop["order"],
            )
            for stop in route_data["stops"]
        ]

    def invalidate(self, route_id: str) -> None:
        """Remove a route from the cache."""

        self._cache.pop(route_id, None)

    def clear(self) -> None:
        """Remove all cached routes."""

        self._cache.clear()

    async def close(self) -> None:
        """Close the HTTP session."""

        if self._session and not self._session.closed:
            await self._session.close()

        self._session = None
