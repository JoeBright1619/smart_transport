from __future__ import annotations

import logging
from typing import Any

import aiohttp

from gps_service.config import settings

logger = logging.getLogger(__name__)

SERVICE_TOKEN_HEADER = "X-" + "Service-Token"
WHOAMI_PATH = "/api/v1/service/whoami"


async def resolve_tenant_id(
    *,
    base_url: str | None = None,
    service_token: str | None = None,
    timeout: float | None = None,
    session: aiohttp.ClientSession | None = None,
) -> str:
    """Ask the backend which tenant this service token belongs to.

    Called once at startup; the returned tenant id is then passed
    explicitly to VehicleFetcher.
    """
    base_url = (base_url or settings.BACKEND_BASE_URL).rstrip("/")
    service_token = service_token or settings.BACKEND_SERVICE_TOKEN
    timeout = timeout if timeout is not None else settings.BACKEND_REQUEST_TIMEOUT

    if not service_token:
        raise RuntimeError(
            "BACKEND_SERVICE_TOKEN is not configured; cannot resolve tenant"
        )

    owns_session = session is None
    if session is None:
        session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout))

    try:
        async with session.get(
            f"{base_url}{WHOAMI_PATH}",
            headers={SERVICE_TOKEN_HEADER: service_token},
        ) as response:
            if response.status != 200:
                body = await response.text()
                raise RuntimeError(
                    f"Backend returned {response.status} for {WHOAMI_PATH}: "
                    f"{body[:200]}"
                )
            payload: dict[str, Any] = await response.json()
    finally:
        if owns_session:
            await session.close()

    tenant_id = (payload.get("data") or {}).get("tenant_id")
    if not tenant_id:
        raise RuntimeError(
            f"Backend response for {WHOAMI_PATH} is missing data.tenant_id"
        )

    logger.info("Resolved service tenant: %s", tenant_id)
    return tenant_id
