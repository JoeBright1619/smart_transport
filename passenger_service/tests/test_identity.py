from __future__ import annotations

import pytest
from aioresponses import aioresponses

from passenger_service.identity import resolve_tenant_id

BACKEND = "http://backend.test"
TOKEN = "stk-universal"
VEHICLE_ID = "veh-abc"


def _detail_url() -> str:
    return f"{BACKEND}/api/v1/service/vehicles/{VEHICLE_ID}"


def _detail_payload(tenant_id: str = "ten-1") -> dict:
    return {
        "data": {
            "id": VEHICLE_ID,
            "tenantId": tenant_id,
            "registrationNumber": "RAD 001 A",
            "model": "Test Bus",
            "seatingCapacity": 45,
            "currentOccupancy": 0,
            "status": "active",
            "engineStatus": "good",
            "completedLoops": 0,
            "lastUpdate": "2026-01-01T00:00:00Z",
        },
        "meta": None,
        "error": None,
    }


async def test_resolve_returns_tenant_id() -> None:
    with aioresponses() as m:
        m.get(_detail_url(), payload=_detail_payload("ten-42"))
        tenant_id = await resolve_tenant_id(
            VEHICLE_ID, base_url=BACKEND, service_token=TOKEN
        )
    assert tenant_id == "ten-42"


async def test_resolve_sends_service_token_header() -> None:
    with aioresponses() as m:
        m.get(_detail_url(), payload=_detail_payload())
        await resolve_tenant_id(VEHICLE_ID, base_url=BACKEND, service_token=TOKEN)

        calls = list(m.requests.values())
        assert calls, "expected a mocked call"
        headers = calls[0][0].kwargs.get("headers") or {}
        assert headers.get("X-Service-Token") == TOKEN


async def test_resolve_raises_on_404() -> None:
    with aioresponses() as m:
        m.get(
            _detail_url(),
            status=404,
            payload={
                "data": None,
                "meta": None,
                "error": {
                    "code": "vehicle_not_found",
                    "message": "Vehicle not found",
                },
            },
        )
        with pytest.raises(RuntimeError) as exc:
            await resolve_tenant_id(VEHICLE_ID, base_url=BACKEND, service_token=TOKEN)
    assert "404" in str(exc.value)
    assert "vehicle_not_found" in str(exc.value)


async def test_resolve_raises_on_500() -> None:
    with aioresponses() as m:
        m.get(_detail_url(), status=500, body="boom")
        with pytest.raises(RuntimeError) as exc:
            await resolve_tenant_id(VEHICLE_ID, base_url=BACKEND, service_token=TOKEN)
    assert "500" in str(exc.value)


async def test_resolve_raises_on_missing_tenant_id() -> None:
    with aioresponses() as m:
        # data present but no tenantId
        m.get(_detail_url(), payload={"data": {"id": VEHICLE_ID}})
        with pytest.raises(RuntimeError) as exc:
            await resolve_tenant_id(VEHICLE_ID, base_url=BACKEND, service_token=TOKEN)
    assert "tenantId" in str(exc.value)


async def test_resolve_raises_on_empty_service_token() -> None:
    with pytest.raises(RuntimeError):
        await resolve_tenant_id(VEHICLE_ID, base_url=BACKEND, service_token="")


async def test_resolve_uses_passed_session_and_does_not_close_it() -> None:
    import aiohttp

    session = aiohttp.ClientSession()
    try:
        with aioresponses() as m:
            m.get(_detail_url(), payload=_detail_payload("ten-9"))
            tenant_id = await resolve_tenant_id(
                VEHICLE_ID,
                base_url=BACKEND,
                service_token=TOKEN,
                session=session,
            )
        assert tenant_id == "ten-9"
        assert session.closed is False
    finally:
        await session.close()
