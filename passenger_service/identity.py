"""Tenant resolution for passenger_service.

Unlike gps_service's whoami-based resolver, passenger_service operates
cross-tenant: its service token is universal (tenant_id IS NULL), so
"which tenant am I" has no answer. The useful question is "which tenant
owns this vehicle" — the vehicle id arrives in a raw MQTT position
event, and downstream calls (e.g. occupancy publish, Task 3.5's
sequence client) need the tenant to scope their work.

This resolver calls the tenant-agnostic backend endpoint added in
backend Task 3.0 (GET /api/v1/service/vehicles/{id}) and reads
data.tenantId (camelCase on the wire — VehicleRead uses APIModel's
alias generator).
"""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)

SERVICE_TOKEN_HEADER = "X-Service-Token"  # nosec
VEHICLE_PATH = "/api/v1/service/vehicles"


async def resolve_tenant_id(
    vehicle_id: str,
    *,
    base_url: str,
    service_token: str,
    timeout: float | None = None,
    session: aiohttp.ClientSession | None = None,
) -> str:
    """Return the tenant id that owns the given vehicle.

    Calls GET /api/v1/service/vehicles/{vehicle_id} and reads
    data.tenantId. Requires a universal service token with
    ``vehicles:read_universal`` scope.

    Raises:
      RuntimeError — non-200 response (including 404 vehicle_not_found),
                     or response is missing data.tenantId.
    """

    if not service_token:
        raise RuntimeError("service_token is required to resolve a tenant")

    url = f"{base_url.rstrip('/')}{VEHICLE_PATH}/{vehicle_id}"
    headers = {SERVICE_TOKEN_HEADER: service_token}

    owns_session = session is None
    if session is None:
        client_timeout = (
            aiohttp.ClientTimeout(total=timeout)
            if timeout is not None
            else aiohttp.ClientTimeout(total=None)
        )
        session = aiohttp.ClientSession(timeout=client_timeout)

    try:
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                body = await response.text()
                raise RuntimeError(
                    f"Backend returned {response.status} for {url}: {body[:200]}"
                )
            payload: dict[str, Any] = await response.json()
    finally:
        if owns_session:
            await session.close()

    # VehicleRead uses APIModel's camelCase alias generator, so the wire
    # field is tenantId, not tenant_id.
    tenant_id = (payload.get("data") or {}).get("tenantId")
    if not tenant_id:
        raise RuntimeError(f"Backend response for {url} is missing data.tenantId")

    logger.info("Resolved tenant for vehicle %s: %s", vehicle_id, tenant_id)
    return tenant_id
