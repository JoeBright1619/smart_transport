from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from passenger_service.config import PassengerServiceSettings
from passenger_service.models.vehicle_info import VehicleInfo
from passenger_service.refresh import refresh_loop


def _vehicle(vehicle_id: str) -> VehicleInfo:
    return VehicleInfo(
        vehicle_id=vehicle_id,
        tenant_id="ten-1",
        route_id="rt-1",
        seating_capacity=40,
        current_occupancy=0,
    )


def _settings(interval: float = 0.01) -> PassengerServiceSettings:
    """Settings with a tiny interval for fast tests."""
    s = PassengerServiceSettings()
    object.__setattr__(s, "VEHICLE_REFRESH_INTERVAL", interval)
    return s


async def _wait_until(predicate, timeout: float = 2.0) -> None:
    """Poll predicate() at 1ms until True or timeout."""
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while not predicate():
        if loop.time() > deadline:
            raise AssertionError(f"predicate not met within {timeout}s")
        await asyncio.sleep(0.001)


async def test_loop_calls_fetchers_periodically() -> None:
    vehicle_fetcher = AsyncMock()
    vehicle_fetcher.fetch_active_vehicles.return_value = [_vehicle("veh-a")]
    pool_fetcher = AsyncMock()
    pool_fetcher.fetch_passenger_ids.return_value = []
    orchestrator = MagicMock()
    orchestrator.release_vehicle.return_value = []

    stop = asyncio.Event()
    task = asyncio.create_task(
        refresh_loop(
            orchestrator=orchestrator,
            vehicle_map_fetcher=vehicle_fetcher,
            pool_fetcher=pool_fetcher,
            settings=_settings(interval=0.01),
            stop_event=stop,
        )
    )
    try:
        await _wait_until(
            lambda: vehicle_fetcher.fetch_active_vehicles.await_count >= 3
        )
    finally:
        stop.set()
        await asyncio.wait_for(task, timeout=1.0)

    assert vehicle_fetcher.fetch_active_vehicles.await_count >= 3
    assert pool_fetcher.fetch_passenger_ids.await_count >= 3


async def test_first_iteration_fetches_immediately() -> None:
    """Departure from gps_service: fetch at t=0, not after interval."""
    vehicle_fetcher = AsyncMock()
    vehicle_fetcher.fetch_active_vehicles.return_value = []
    pool_fetcher = AsyncMock()
    pool_fetcher.fetch_passenger_ids.return_value = []
    orchestrator = MagicMock()
    orchestrator.release_vehicle.return_value = []

    stop = asyncio.Event()
    task = asyncio.create_task(
        refresh_loop(
            orchestrator=orchestrator,
            vehicle_map_fetcher=vehicle_fetcher,
            pool_fetcher=pool_fetcher,
            settings=_settings(interval=60.0),  # long; would fail if wait-first
            stop_event=stop,
        )
    )
    try:
        # First fetch should complete almost immediately.
        await _wait_until(
            lambda: vehicle_fetcher.fetch_active_vehicles.await_count >= 1,
            timeout=1.0,
        )
        assert pool_fetcher.fetch_passenger_ids.await_count >= 1
    finally:
        stop.set()
        await asyncio.wait_for(task, timeout=1.0)


async def test_loop_exits_promptly_on_stop_event() -> None:
    vehicle_fetcher = AsyncMock()
    vehicle_fetcher.fetch_active_vehicles.return_value = []
    pool_fetcher = AsyncMock()
    pool_fetcher.fetch_passenger_ids.return_value = []
    orchestrator = MagicMock()
    orchestrator.release_vehicle.return_value = []

    stop = asyncio.Event()
    task = asyncio.create_task(
        refresh_loop(
            orchestrator=orchestrator,
            vehicle_map_fetcher=vehicle_fetcher,
            pool_fetcher=pool_fetcher,
            settings=_settings(interval=60.0),
            stop_event=stop,
        )
    )
    # Let the first iteration finish.
    await _wait_until(lambda: vehicle_fetcher.fetch_active_vehicles.await_count >= 1)
    # Now set stop and assert it exits well before 60s.
    stop.set()
    await asyncio.wait_for(task, timeout=1.0)


async def test_loop_releases_disappeared_vehicles() -> None:
    """First fetch returns veh-a, veh-b; second returns only veh-a.
    veh-b must be released and the map updated to exclude it."""
    responses = [
        [_vehicle("veh-a"), _vehicle("veh-b")],
        [_vehicle("veh-a")],
        [_vehicle("veh-a")],  # subsequent iterations
    ]
    call_count = [0]

    async def _fetch():
        idx = min(call_count[0], len(responses) - 1)
        call_count[0] += 1
        return responses[idx]

    vehicle_fetcher = MagicMock()
    vehicle_fetcher.fetch_active_vehicles = _fetch
    pool_fetcher = AsyncMock()
    pool_fetcher.fetch_passenger_ids.return_value = []
    orchestrator = MagicMock()
    orchestrator.release_vehicle.return_value = ["pas-1", "pas-2"]

    stop = asyncio.Event()
    task = asyncio.create_task(
        refresh_loop(
            orchestrator=orchestrator,
            vehicle_map_fetcher=vehicle_fetcher,
            pool_fetcher=pool_fetcher,
            settings=_settings(interval=0.01),
            stop_event=stop,
        )
    )
    try:
        await _wait_until(lambda: call_count[0] >= 3)
    finally:
        stop.set()
        await asyncio.wait_for(task, timeout=1.0)

    orchestrator.release_vehicle.assert_called_once_with("veh-b")
    # set_vehicle_map called at least 3 times; last call should have only veh-a
    assert orchestrator.set_vehicle_map.call_count >= 3
    last_call_map = orchestrator.set_vehicle_map.call_args_list[-1].args[0]
    assert set(last_call_map.keys()) == {"veh-a"}


async def test_loop_survives_vehicle_fetch_failure(monkeypatch) -> None:
    monkeypatch.setattr("passenger_service.refresh._RETRY_ATTEMPTS", 1)
    monkeypatch.setattr("passenger_service.refresh._RETRY_DELAY", 0.0)

    call_count = [0]

    async def _fetch():
        call_count[0] += 1
        if call_count[0] == 1:
            raise RuntimeError("transient")
        return [_vehicle("veh-a")]

    vehicle_fetcher = MagicMock()
    vehicle_fetcher.fetch_active_vehicles = _fetch
    pool_fetcher = AsyncMock()
    pool_fetcher.fetch_passenger_ids.return_value = []
    orchestrator = MagicMock()
    orchestrator.release_vehicle.return_value = []

    stop = asyncio.Event()
    task = asyncio.create_task(
        refresh_loop(
            orchestrator=orchestrator,
            vehicle_map_fetcher=vehicle_fetcher,
            pool_fetcher=pool_fetcher,
            settings=_settings(interval=0.01),
            stop_event=stop,
        )
    )
    try:
        await _wait_until(lambda: call_count[0] >= 2)
    finally:
        stop.set()
        await asyncio.wait_for(task, timeout=1.0)

    # Second call succeeded, map updated.
    orchestrator.set_vehicle_map.assert_called_with(
        {"veh-a": pytest.ANY}
        if False
        else orchestrator.set_vehicle_map.call_args_list[-1].args[0]
    )
    # Simpler assertion:
    last_map = orchestrator.set_vehicle_map.call_args_list[-1].args[0]
    assert set(last_map.keys()) == {"veh-a"}


async def test_loop_survives_pool_fetch_failure(monkeypatch) -> None:
    monkeypatch.setattr("passenger_service.refresh._RETRY_ATTEMPTS", 1)
    monkeypatch.setattr("passenger_service.refresh._RETRY_DELAY", 0.0)

    pool_calls = [0]

    async def _fetch():
        pool_calls[0] += 1
        if pool_calls[0] == 1:
            raise RuntimeError("transient")
        return []

    vehicle_fetcher = AsyncMock()
    vehicle_fetcher.fetch_active_vehicles.return_value = [_vehicle("veh-a")]
    pool_fetcher = MagicMock()
    pool_fetcher.fetch_passenger_ids = _fetch
    orchestrator = MagicMock()
    orchestrator.release_vehicle.return_value = []

    stop = asyncio.Event()
    task = asyncio.create_task(
        refresh_loop(
            orchestrator=orchestrator,
            vehicle_map_fetcher=vehicle_fetcher,
            pool_fetcher=pool_fetcher,
            settings=_settings(interval=0.01),
            stop_event=stop,
        )
    )
    try:
        await _wait_until(lambda: pool_calls[0] >= 2)
    finally:
        stop.set()
        await asyncio.wait_for(task, timeout=1.0)

    # Vehicle map still refreshed despite pool failure.
    assert orchestrator.set_vehicle_map.call_count >= 2
