from __future__ import annotations

import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer

from gps_service.vehicle_tracker.fetcher import VehicleFetcher


def _vehicle(
    vehicle_id: str,
    route_id: str | None = "route-1",
    lat: float | None = -1.94,
    lng: float | None = 30.05,
    status: str = "active",
    fuel: int | None = 75,
    engine_status: str = "good",
) -> dict:
    return {
        "id": vehicle_id,
        "registrationNumber": f"REG-{vehicle_id}",
        "model": "Test",
        "seatingCapacity": 45,
        "currentOccupancy": 10,
        "status": status,
        "speed": 30,
        "heading": 90,
        "fuel": fuel,
        "engineStatus": engine_status,
        "routeId": route_id,
        "driverId": None,
        "plannedLoops": 5,
        "completedLoops": 1,
        "lastUpdate": "2026-04-08T17:00:00Z",
        "currentLocation": (
            {"lat": lat, "lng": lng} if lat is not None and lng is not None else None
        ),
    }


async def _start_server(handler) -> TestServer:
    app = web.Application()
    app.router.add_get("/api/v1/vehicles", handler)
    server = TestServer(app)
    await server.start_server()
    return server


@pytest.mark.asyncio
async def test_fetch_single_page():
    async def handler(request: web.Request) -> web.Response:
        assert request.headers["X-Service-Token"] == "secret"
        assert request.query["status"] == "active"
        assert request.query["page"] == "1"
        return web.json_response(
            {
                "data": [_vehicle("veh-1"), _vehicle("veh-2")],
                "meta": {"total": 2, "page": 1, "pageSize": 100},
                "error": None,
            }
        )

    server = await _start_server(handler)
    try:
        async with VehicleFetcher(
            tenant_id="ten-1",
            base_url=str(server.make_url("")).rstrip("/"),
            service_token="secret",
            page_size=100,
        ) as fetcher:
            vehicles = await fetcher.fetch_active_vehicles()
    finally:
        await server.close()

    assert {v.vehicle_id for v in vehicles} == {"veh-1", "veh-2"}
    assert all(v.tenant_id == "ten-1" for v in vehicles)
    assert all(v.device_id == f"sim-{v.vehicle_id}" for v in vehicles)
    assert vehicles[0].fuel == 75.0


@pytest.mark.asyncio
async def test_fetch_follows_pagination():
    calls = {"n": 0}

    async def handler(request: web.Request) -> web.Response:
        calls["n"] += 1
        page = int(request.query["page"])
        data = [_vehicle(f"veh-{page}-1"), _vehicle(f"veh-{page}-2")]
        return web.json_response(
            {
                "data": data,
                "meta": {"total": 4, "page": page, "pageSize": 2},
                "error": None,
            }
        )

    server = await _start_server(handler)
    try:
        async with VehicleFetcher(
            tenant_id="ten-1",
            base_url=str(server.make_url("")).rstrip("/"),
            service_token="secret",
            page_size=2,
        ) as fetcher:
            vehicles = await fetcher.fetch_active_vehicles()
    finally:
        await server.close()

    assert calls["n"] == 2
    assert len(vehicles) == 4


@pytest.mark.asyncio
async def test_skips_vehicle_without_route():
    async def handler(request: web.Request) -> web.Response:
        return web.json_response(
            {
                "data": [
                    _vehicle("veh-ok"),
                    _vehicle("veh-no-route", route_id=None),
                    _vehicle("veh-no-loc", lat=None, lng=None),
                ],
                "meta": {"total": 3, "page": 1, "pageSize": 100},
                "error": None,
            }
        )

    server = await _start_server(handler)
    try:
        async with VehicleFetcher(
            tenant_id="ten-1",
            base_url=str(server.make_url("")).rstrip("/"),
            service_token="secret",
        ) as fetcher:
            vehicles = await fetcher.fetch_active_vehicles()
    finally:
        await server.close()

    assert [v.vehicle_id for v in vehicles] == ["veh-ok"]


@pytest.mark.asyncio
async def test_raises_on_non_200():
    async def handler(request: web.Request) -> web.Response:
        return web.json_response({"error": "nope"}, status=401)

    server = await _start_server(handler)
    try:
        async with VehicleFetcher(
            tenant_id="ten-1",
            base_url=str(server.make_url("")).rstrip("/"),
            service_token="bad",
        ) as fetcher:
            with pytest.raises(RuntimeError, match="401"):
                await fetcher.fetch_active_vehicles()
    finally:
        await server.close()


def test_missing_tenant_raises():
    with pytest.raises(ValueError, match="tenant_id is required"):
        VehicleFetcher(tenant_id="", service_token="secret")


def test_missing_token_raises(monkeypatch):
    monkeypatch.setattr("gps_service.config.settings.BACKEND_SERVICE_TOKEN", "")
    with pytest.raises(ValueError, match="BACKEND_SERVICE_TOKEN"):
        VehicleFetcher(tenant_id="ten-1", service_token=None)


@pytest.mark.asyncio
async def test_engine_status_and_operational_status_are_passed_through():
    async def handler(request: web.Request) -> web.Response:
        return web.json_response(
            {
                "data": [
                    _vehicle("veh-good", status="active", engine_status="good"),
                    _vehicle("veh-warn", status="idle", engine_status="warning"),
                    _vehicle("veh-crit", status="active", engine_status="critical"),
                ],
                "meta": {"total": 3, "page": 1, "pageSize": 100},
                "error": None,
            }
        )

    server = await _start_server(handler)
    try:
        async with VehicleFetcher(
            tenant_id="ten-1",
            base_url=str(server.make_url("")).rstrip("/"),
            service_token="secret",
        ) as fetcher:
            vehicles = await fetcher.fetch_active_vehicles()
    finally:
        await server.close()

    by_id = {v.vehicle_id: v for v in vehicles}
    assert by_id["veh-good"].status == "active"
    assert by_id["veh-good"].engine_status == "good"
    assert by_id["veh-warn"].status == "idle"
    assert by_id["veh-warn"].engine_status == "warning"
    assert by_id["veh-crit"].status == "active"
    assert by_id["veh-crit"].engine_status == "critical"
