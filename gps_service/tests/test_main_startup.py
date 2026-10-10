# gps_service/tests/test_main_startup.py
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gps_service.models.gps_data import VehicleState
import gps_service.main as main_module


def _vehicle(vid: str) -> VehicleState:
    return VehicleState(
        vehicle_id=vid,
        device_id=f"dev-{vid}",
        tenant_id="tenant-1",
        route_id="route-1",
        latitude=1.0,
        longitude=2.0,
        speed=10.0,
        heading=90.0,
        status="active",
        engine_status="good",
        fuel=80.0,
        last_updated="2026-01-01T00:00:00Z",
    )


@pytest.mark.asyncio
async def test_startup_shutdown_happy_path():
    vehicles = [_vehicle("v1"), _vehicle("v2")]

    fake_state_manager = MagicMock()
    fake_state_manager.all.return_value = []

    fake_orchestrator = MagicMock()
    fake_orchestrator.run = AsyncMock(side_effect=lambda: asyncio.sleep(3600))
    fake_orchestrator.stop = MagicMock()
    fake_orchestrator.sync_vehicles = MagicMock()

    fake_publisher = MagicMock()

    fake_route_cache = MagicMock()
    fake_route_cache.close = AsyncMock()

    fake_fetcher = MagicMock()
    fake_fetcher.fetch_active_vehicles = AsyncMock(return_value=vehicles)
    fake_fetcher.__aenter__ = AsyncMock(return_value=fake_fetcher)
    fake_fetcher.__aexit__ = AsyncMock(return_value=None)

    shutdown = asyncio.Event()

    with patch.object(
        main_module, "resolve_tenant_id", AsyncMock(return_value="tenant-1")
    ), patch.object(
        main_module, "MQTTPublisher", return_value=fake_publisher
    ), patch.object(
        main_module, "RouteCache", return_value=fake_route_cache
    ), patch.object(
        main_module, "VehicleStateManager", return_value=fake_state_manager
    ), patch.object(
        main_module, "VehicleFetcher", return_value=fake_fetcher
    ), patch.object(
        main_module, "SimulatorOrchestrator", return_value=fake_orchestrator
    ):
        run_task = asyncio.create_task(main_module._run(shutdown=shutdown))

        # Let startup run through seeding.
        for _ in range(100):
            await asyncio.sleep(0)
            if fake_state_manager.set.call_count == len(vehicles):
                break

        shutdown.set()
        await asyncio.wait_for(run_task, timeout=5)

    fake_publisher.connect.assert_called_once()
    assert fake_state_manager.set.call_count == len(vehicles)
    fake_fetcher.fetch_active_vehicles.assert_awaited_once()

    fake_orchestrator.stop.assert_called_once()
    fake_fetcher.__aexit__.assert_awaited_once()
    fake_route_cache.close.assert_awaited_once()
    fake_publisher.disconnect.assert_called_once()
    fake_state_manager.save.assert_called_once()
