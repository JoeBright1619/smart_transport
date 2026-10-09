from __future__ import annotations

import logging
from typing import Any

import aiohttp

from gps_service.config import settings
from gps_service.models.gps_data import VehicleState
from gps_service.vehicle_tracker.wire import normalize_keys

logger = logging.getLogger(__name__)

SERVICE_TOKEN_HEADER = "X-" + "Service-Token"
ACTIVE_STATUS = "active"
LIST_PATH = "/api/v1/vehicles"


class VehicleFetcher:
    """Fetch active vehicles for one tenant from the backend API."""

    def __init__(
        self,
        tenant_id: str,
        *,
        base_url: str | None = None,
        service_token: str | None = None,
        timeout: float | None = None,
        page_size: int | None = None,
        device_id_prefix: str | None = None,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        if not tenant_id:
            raise ValueError("tenant_id is required")
        if not (service_token or settings.BACKEND_SERVICE_TOKEN):
            raise ValueError("BACKEND_SERVICE_TOKEN is not configured")

        self.tenant_id = tenant_id
        self.base_url = (base_url or settings.BACKEND_BASE_URL).rstrip("/")
        self.service_token = service_token or settings.BACKEND_SERVICE_TOKEN
        self.timeout = (
            timeout if timeout is not None else settings.BACKEND_REQUEST_TIMEOUT
        )
        self.page_size = page_size or settings.BACKEND_PAGE_SIZE
        self.device_id_prefix = device_id_prefix or settings.DEVICE_ID_PREFIX

        self._session = session
        self._owns_session = session is None

    async def __aenter__(self) -> VehicleFetcher:
        await self._ensure_session()
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    async def close(self) -> None:
        if self._owns_session and self._session is not None:
            await self._session.close()
            self._session = None

    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
            self._owns_session = True
        return self._session

    def _headers(self) -> dict[str, str]:
        return {SERVICE_TOKEN_HEADER: self.service_token}

    async def fetch_active_vehicles(self) -> list[VehicleState]:
        """Fetch all active vehicles for this tenant, following pagination."""
        session = await self._ensure_session()
        results: list[VehicleState] = []
        page = 1

        while True:
            params = {
                "status": ACTIVE_STATUS,
                "page": page,
                "pageSize": self.page_size,
            }

            async with session.get(
                f"{self.base_url}{LIST_PATH}",
                params=params,
                headers=self._headers(),
            ) as response:
                if response.status != 200:
                    body = await response.text()
                    raise RuntimeError(
                        f"Backend returned {response.status} for "
                        f"{LIST_PATH}: {body[:200]}"
                    )
                raw = await response.json()
                payload = normalize_keys(raw)

            items = payload.get("data") or []
            for item in items:
                mapped = self._map_vehicle(item)
                if mapped is not None:
                    results.append(mapped)

            meta = payload.get("meta") or {}
            total = meta.get("total", 0)
            returned_page_size = meta.get("pageSize", self.page_size)

            if not items or page * returned_page_size >= total:
                break
            page += 1

        logger.info(
            "Fetched %d active vehicles for tenant %s",
            len(results),
            self.tenant_id,
        )
        return results

    def _map_vehicle(self, item: dict[str, Any]) -> VehicleState | None:
        vehicle_id = item.get("id")
        route_id = item.get("route_id")

        if not vehicle_id:
            logger.warning("Skipping vehicle with no id: %s", item)
            return None

        if not route_id:
            logger.warning("Skipping vehicle %s: no route_id", vehicle_id)
            return None

        location = item.get("current_location") or {}
        latitude = location.get("lat")
        longitude = location.get("lng")

        if latitude is None or longitude is None:
            logger.warning("Skipping vehicle %s: no current location", vehicle_id)
            return None

        return VehicleState(
            vehicle_id=vehicle_id,
            device_id=f"{self.device_id_prefix}-{vehicle_id}",
            tenant_id=self.tenant_id,
            route_id=route_id,
            latitude=float(latitude),
            longitude=float(longitude),
            speed=float(item.get("speed") or 0.0),
            heading=float(item.get("heading") or 0.0),
            status=item.get("status") or "active",
            engine_status=item.get("engine_status") or "good",
            fuel=float(item["fuel"] if item.get("fuel") is not None else 100.0),
            last_updated=item.get("last_update"),
        )
