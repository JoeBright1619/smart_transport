from __future__ import annotations

import aiohttp

from passenger_service.models.vehicle_info import VehicleInfo
from passenger_service.wire import normalize_keys

_PAGE_SIZE = 100  # backend VehicleRead caps page_size at le=100


class VehicleMapFetcher:
    """Fetch active, route-assigned vehicles from the Smart Transport backend."""

    def __init__(self, base_url: str, service_token: str) -> None:
        if not service_token:
            raise ValueError("service_token must not be empty")
        self.base_url = base_url.rstrip("/")
        self._service_token = service_token
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def fetch_active_vehicles(self) -> list[VehicleInfo]:
        """Return all active, route-assigned vehicles across all pages."""

        results: list[VehicleInfo] = []
        seen = 0
        page = 1

        while True:
            payload = await self._fetch_page(page)
            data = payload.get("data") or []

            for raw in data:
                info = _to_vehicle_info(normalize_keys(raw))
                if info is not None:
                    results.append(info)

            seen += len(data)
            meta = payload.get("meta") or {}
            total = int(meta.get("total") or 0)

            # Terminate when we've consumed everything the backend reports,
            # OR when the backend returns an empty page (defensive against
            # total being wrong / zero). `seen` counts raw rows, not kept
            # rows, because skipped rows (no route_id) still count toward
            # total — using len(results) here would loop forever when any
            # vehicle is skipped.
            if not data or seen >= total:
                break

            page += 1

        return results

    async def _fetch_page(self, page: int) -> dict:
        session = await self._get_session()

        url = f"{self.base_url}/api/v1/service/vehicles"
        params = {"status": "active", "page": page, "page_size": _PAGE_SIZE}
        headers = {"X-Service-Token": self._service_token}

        async with session.get(url, params=params, headers=headers) as response:
            response.raise_for_status()
            return await response.json()

    async def close(self) -> None:
        """Close the underlying HTTP session."""

        if self._session and not self._session.closed:
            await self._session.close()
        self._session = None


def _to_vehicle_info(raw: dict) -> VehicleInfo | None:
    """Map a normalized VehicleRead dict to VehicleInfo.

    Returns None when the vehicle has no route assignment — those rows
    are skipped per the brief. Raises if a required field the brief says
    must be present is missing, because silently skipping them would
    hide a backend contract break.
    """

    route_id = raw.get("route_id")
    if not route_id:
        return None

    return VehicleInfo(
        vehicle_id=raw["id"],
        tenant_id=raw["tenant_id"],
        route_id=route_id,
        seating_capacity=int(raw.get("seating_capacity") or 0),
        current_occupancy=int(raw.get("current_occupancy") or 0),
    )
