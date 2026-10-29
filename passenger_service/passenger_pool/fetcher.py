from __future__ import annotations

import time
from typing import Sequence

import aiohttp

from passenger_service.wire import normalize_keys

_DEFAULT_PAGE_SIZE = 100  # backend PassengerListItem caps page_size at le=100


class PassengerPoolFetcher:
    """Fetches the universal passenger id pool from the backend.

    "Universal" here means the backend endpoint is not tenant-scoped:
    GET /api/v1/passengers returns passengers across all tenants when
    called with a universal service token (scopes passengers:read_universal).

    The fetcher caches the last successful fetch. cached_ids() is a pure
    reader; the caller is responsible for calling fetch_passenger_ids()
    periodically (VEHICLE_REFRESH_INTERVAL from settings), in the same
    loop that refreshes the vehicle map. No background task lives inside
    the fetcher — see the design rationale in task 3.4.
    """

    def __init__(
        self,
        base_url: str,
        service_token: str,
        refresh_interval: float = 60.0,
        page_size: int = _DEFAULT_PAGE_SIZE,
    ) -> None:
        if not service_token:
            raise ValueError("service_token must not be empty")
        self.base_url = base_url.rstrip("/")
        self._service_token = service_token
        self._refresh_interval = refresh_interval
        self._page_size = page_size

        self._cached_ids: tuple[str, ...] = ()
        self._expires_at: float = 0.0
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def fetch_passenger_ids(self) -> list[str]:
        """Fetch every passenger id from the backend, paginating until
        meta.total is satisfied. Updates the cache on success.

        Does not include a tenant_id query param — passengers are
        universal (design §7), and the backend rejects it as unknown.
        """

        ids: list[str] = []
        seen = 0
        page = 1

        while True:
            payload = await self._fetch_page(page)
            data = payload.get("data") or []

            for raw in data:
                normalized = normalize_keys(raw)
                # PassengerListItem may carry extra fields; we only need id.
                ids.append(normalized["id"])

            seen += len(data)
            meta = payload.get("meta") or {}
            total = int(meta.get("total") or 0)

            # Terminate when consumed rows reach the backend-reported total,
            # or when a page comes back empty (defensive). seen counts raw
            # rows, not kept rows, mirroring the vehicle fetcher's pagination.
            if not data or seen >= total:
                break

            page += 1

        self._cached_ids = tuple(ids)
        self._expires_at = time.monotonic() + self._refresh_interval
        return ids

    async def _fetch_page(self, page: int) -> dict:
        session = await self._get_session()

        url = f"{self.base_url}/api/v1/passengers"
        params = {"page": page, "page_size": self._page_size}
        headers = {"X-Service-Token": self._service_token}

        async with session.get(url, params=params, headers=headers) as response:
            response.raise_for_status()
            return await response.json()

    def cached_ids(self) -> Sequence[str]:
        """Return the last fetched ids (empty tuple before the first fetch).

        Pure reader — does not consult the TTL or trigger a refetch.
        The caller decides when to call fetch_passenger_ids() again,
        typically driven by VEHICLE_REFRESH_INTERVAL in the same loop
        that refreshes the vehicle map.
        """

        return self._cached_ids

    def is_stale(self) -> bool:
        """True if the cache has expired and the caller should refresh.

        Exposed so the caller's loop can cheaply decide whether to call
        fetch_passenger_ids() this tick. Not required by the brief, but
        keeps TTL policy out of callers.
        """

        return time.monotonic() >= self._expires_at

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
        self._session = None
