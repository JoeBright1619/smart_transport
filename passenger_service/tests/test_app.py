"""Tests for the FastAPI app lifespan and endpoints."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from passenger_service.api.app import create_app


@pytest.fixture
def patched_lifespan(monkeypatch):
    """Patch MQTT classes and refresh_loop so tests don't touch the broker
    or spin a real background task against mocked fetchers."""

    publisher_mock = MagicMock()
    subscriber_mock = MagicMock()
    subscriber_mock.subscribed = True

    # MQTTPublisher and MQTTSubscriber classes are patched at the module level.
    monkeypatch.setattr(
        "passenger_service.api.app.MQTTPublisher",
        lambda *a, **k: publisher_mock,
    )
    monkeypatch.setattr(
        "passenger_service.api.app.MQTTSubscriber",
        lambda *a, **k: subscriber_mock,
    )

    # Fake refresh_loop that sets first_iteration_done and yields until
    # stop_event is set.
    async def fake_refresh_loop(
        *,
        orchestrator,
        vehicle_map_fetcher,
        pool_fetcher,
        settings,
        stop_event,
        first_iteration_done=None,
    ):
        # Populate the map directly (so /status has something to report).
        from passenger_service.models.vehicle_info import VehicleInfo

        orchestrator.set_vehicle_map(
            {
                "veh-a": VehicleInfo(
                    vehicle_id="veh-a",
                    tenant_id="ten-1",
                    route_id="rt-1",
                    seating_capacity=40,
                    current_occupancy=0,
                )
            }
        )
        if first_iteration_done is not None:
            first_iteration_done.set()
        try:
            await stop_event.wait()
        except asyncio.CancelledError:
            return

    monkeypatch.setattr(
        "passenger_service.api.app.refresh_loop",
        fake_refresh_loop,
    )

    # Fetchers/clients are built inside lifespan; patch their close() to
    # be awaitable no-ops so shutdown doesn't try real I/O.
    for cls_name in (
        "RouteCache",
        "VehicleMapFetcher",
        "PassengerPoolFetcher",
        "SequenceClient",
    ):
        # We can't easily monkeypatch the class methods' close because the
        # instances are created inside lifespan. Instead, patch the classes
        # themselves to return mocks.
        pass
    # Patch the HTTP-client classes to be inert mocks.
    for name in (
        "RouteCache",
        "VehicleMapFetcher",
        "PassengerPoolFetcher",
        "SequenceClient",
    ):
        mock_cls = MagicMock()
        mock_instance = MagicMock()
        mock_instance.close = AsyncMock()
        mock_cls.return_value = mock_instance
        monkeypatch.setattr(f"passenger_service.api.app.{name}", mock_cls)

    return {
        "publisher": publisher_mock,
        "subscriber": subscriber_mock,
    }


async def test_health_returns_envelope(patched_lifespan) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        async with app.router.lifespan_context(app):
            r = await client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"data": {"status": "ok"}, "meta": None, "error": None}


async def test_status_returns_expected_shape(patched_lifespan) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        async with app.router.lifespan_context(app):
            r = await client.get("/status")
    assert r.status_code == 200
    body = r.json()
    assert body["error"] is None
    assert body["meta"] is None
    data = body["data"]
    assert isinstance(data["mqtt_connected"], bool)
    assert isinstance(data["vehicles_tracked"], int)
    assert isinstance(data["events_published"], int)
    assert isinstance(data["uptime_seconds"], float)
    # Fake refresh populated veh-a, so we should see it.
    assert data["vehicles_tracked"] == 1


async def test_lifespan_starts_and_stops_cleanly(patched_lifespan) -> None:
    app = create_app()
    # Just entering and exiting the lifespan must not raise.
    async with app.router.lifespan_context(app):
        # The publisher was connected and subscriber started.
        patched_lifespan["publisher"].connect.assert_called_once()
        patched_lifespan["subscriber"].start.assert_called_once()
    # And on shutdown:
    patched_lifespan["subscriber"].stop.assert_called_once()
    patched_lifespan["publisher"].disconnect.assert_called_once()
