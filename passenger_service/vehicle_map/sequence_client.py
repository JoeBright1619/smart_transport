from __future__ import annotations

import aiohttp

# 404 error codes that legitimately mean "no sequence yet" (return 0).
# Any other 404, or an unparseable 404 body, is treated as a hard error.
_NO_SEQUENCE_CODES = frozenset({"vehicle_not_found", "no_arrival_records"})

# Backend wire field for LatestArrivalSequenceRead, camelCase per
# APIModel's alias generator (project context §2.2 / §5).
_SEQUENCE_FIELD = "arrivalSequence"


class SequenceClient:
    """Read a vehicle's latest arrival sequence from the backend.

    Calls GET /api/v1/service/vehicles/{id}/latest-arrival-sequence
    (backend Task 3.0). Auth: universal service token carrying
    ``vehicles:read_universal``.

    404 with code ``vehicle_not_found`` or ``no_arrival_records`` means
    "start from 0" and returns 0. Any other 404, any 5xx, and network /
    timeout errors raise — the caller must not guess 0 on a transient
    failure.
    """

    def __init__(
        self,
        base_url: str,
        service_token: str,
        timeout: float = 10.0,
    ) -> None:
        if not service_token:
            raise ValueError("service_token must not be empty")
        self.base_url = base_url.rstrip("/")
        self._service_token = service_token
        self._timeout = timeout
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self._timeout)
            )
        return self._session

    async def fetch_latest_sequence(self, vehicle_id: str) -> int:
        """Return the vehicle's latest arrival sequence, or 0 if the
        vehicle exists with no records / does not exist.
        """

        session = await self._get_session()
        url = (
            f"{self.base_url}/api/v1/service/vehicles/"
            f"{vehicle_id}/latest-arrival-sequence"
        )
        headers = {"X-Service-Token": self._service_token}

        async with session.get(url, headers=headers) as response:
            if response.status == 404:
                # Best-effort parse; a 404 we cannot classify is a hard error.
                try:
                    payload = await response.json()
                except Exception:
                    payload = {}
                code = (
                    (payload.get("error") or {}).get("code")
                    if isinstance(payload, dict)
                    else None
                )
                if code in _NO_SEQUENCE_CODES:
                    return 0
                raise aiohttp.ClientResponseError(
                    request_info=response.request_info,
                    history=response.history,
                    status=response.status,
                    message=(
                        f"Unexpected 404 for {url} "
                        f"(code={code!r}); expected one of "
                        f"{sorted(_NO_SEQUENCE_CODES)}"
                    ),
                    headers=response.headers,
                )

            # 2xx, 5xx, etc.: raise_for_status handles non-2xx uniformly.
            response.raise_for_status()
            payload = await response.json()

        data = payload.get("data") or {}
        value = data.get(_SEQUENCE_FIELD)
        if value is None:
            raise ValueError(
                f"Backend response for {url} is missing data.{_SEQUENCE_FIELD}"
            )
        return int(value)

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
        self._session = None
