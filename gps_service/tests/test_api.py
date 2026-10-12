from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import contextlib

from gps_service.models.gps_data import VehicleState
import gps_service.api.app as app_module


def _vehicle(vid: str, status: str = "active") -> VehicleState:
    return VehicleState(
        vehicle_id=vid,
        device_id=f"dev-{vid}",
        tenant_id="tenant-1",
        route_id="route-1",
        latitude=1.0,
        longitude=2.0,
        speed=10.0,
        heading=90.0,
        status=status,  # type: ignore[arg-type]
        engine_status="good",
        fuel=80.0,
        last_updated="2026-01-01T00:00:00Z",
    )


@pytest.mark.asyncio
async def test_health_returns_ok():
    with _patched_collaborators(vehicles=[_vehicle("v1")]):
        app = app_module.create_app()
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            # Manually enter the lifespan.
            async with app.router.lifespan_context(app):
                resp = await client.get("/health")
                assert resp.status_code == 200
                assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_status_reports_state():
    vehicles = [_vehicle("v1"), _vehicle("v2"), _vehicle("v3", status="idle")]

    fake_state_manager = MagicMock()
    fake_state_manager.all.return_value = vehicles

    with _patched_collaborators(vehicles=vehicles, state_manager=fake_state_manager):
        app = app_module.create_app()
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            async with app.router.lifespan_context(app):
                resp = await client.get("/status")

    assert resp.status_code == 200
    body = resp.json()
    assert body["error"] is None
    assert body["data"]["tenant_id"] == "tenant-1"
    assert body["data"]["mqtt_connected"] is True
    assert body["data"]["active_vehicles"] == 2  # v3 is idle
    assert isinstance(body["data"]["uptime_seconds"], float)


class _FakeOrchestrator:
    def __init__(self, *_args, **_kwargs):
        self._stop = asyncio.Event()
        self.sync_vehicles = MagicMock()
        self.stop_called = False

    async def run(self) -> None:
        await self._stop.wait()

    def stop(self) -> None:
        self.stop_called = True
        self._stop.set()


@contextlib.contextmanager
def _patched_collaborators(vehicles, state_manager=None):
    fake_publisher = MagicMock()
    fake_publisher._connected = True

    fake_route_cache = MagicMock()
    fake_route_cache.close = AsyncMock()

    if state_manager is None:
        sm = MagicMock()
        sm.all.return_value = vehicles
    else:
        sm = state_manager

    fake_fetcher = MagicMock()
    fake_fetcher.fetch_active_vehicles = AsyncMock(return_value=vehicles)
    fake_fetcher.__aenter__ = AsyncMock(return_value=fake_fetcher)
    fake_fetcher.__aexit__ = AsyncMock(return_value=None)

    with patch.object(
        app_module, "resolve_tenant_id", AsyncMock(return_value="tenant-1")
    ), patch.object(
        app_module, "MQTTPublisher", return_value=fake_publisher
    ), patch.object(
        app_module, "RouteCache", return_value=fake_route_cache
    ), patch.object(app_module, "VehicleStateManager", return_value=sm), patch.object(
        app_module, "VehicleFetcher", return_value=fake_fetcher
    ), patch.object(app_module, "SimulatorOrchestrator", _FakeOrchestrator):
        yield
