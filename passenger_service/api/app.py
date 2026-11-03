"""FastAPI app for passenger_service.

Lifespan wiring: builds all collaborators once, starts the periodic
refresh loop, connects the MQTT publisher and subscriber, and waits
for the first refresh iteration before subscribing to positions.

Departures from gps_service's app.py, noted inline:

- No startup tenant resolution. passenger_service is cross-tenant; the
  tenant comes from each inbound position event's payload. The
  universal service token carries both passengers:read_universal and
  vehicles:read_universal (Task 3.0).
- No initial fetch in lifespan. refresh_loop fetches at t=0; we wait
  for its first_iteration_done event before subscribing, so the map is
  populated (or has been attempted) before any position arrives.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any, AsyncIterator

from fastapi import FastAPI, Request

from passenger_service.config import settings
from passenger_service.detection.orchestrator import ArrivalOrchestrator
from passenger_service.detection.state import VehicleStateStore
from passenger_service.models.position import PositionEvent
from passenger_service.mqtt.publisher import MQTTPublisher
from passenger_service.mqtt.subscriber import MQTTSubscriber
from passenger_service.passenger_pool.fetcher import PassengerPoolFetcher
from passenger_service.refresh import refresh_loop
from passenger_service.route_cache.cache import RouteCache
from passenger_service.vehicle_map.fetcher import VehicleMapFetcher
from passenger_service.vehicle_map.sequence_client import SequenceClient

logger = logging.getLogger(__name__)

_REFRESH_STOP_TIMEOUT_S = 5.0
_FIRST_REFRESH_TIMEOUT_S = 30.0


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # --- Collaborators that don't need the event loop ---
    route_cache = RouteCache(
        backend_url=settings.BACKEND_BASE_URL,
        ttl=60.0,
    )
    vehicle_map_fetcher = VehicleMapFetcher(
        base_url=settings.BACKEND_BASE_URL,
        service_token=settings.PASSENGER_POOL_SERVICE_TOKEN,
    )
    pool_fetcher = PassengerPoolFetcher(
        base_url=settings.BACKEND_BASE_URL,
        service_token=settings.PASSENGER_POOL_SERVICE_TOKEN,
        refresh_interval=settings.VEHICLE_REFRESH_INTERVAL,
    )
    sequence_client = SequenceClient(
        base_url=settings.BACKEND_BASE_URL,
        service_token=settings.PASSENGER_POOL_SERVICE_TOKEN,
        timeout=settings.BACKEND_REQUEST_TIMEOUT,
    )
    state_store = VehicleStateStore()

    # --- MQTT publisher (used by the orchestrator) ---
    publisher = MQTTPublisher()
    publisher.connect()

    # --- Orchestrator ---
    orchestrator = ArrivalOrchestrator(
        state_store=state_store,
        route_cache=route_cache,
        sequence_client=sequence_client,
        pool_fetcher=pool_fetcher,
        publisher=publisher,
        settings=settings,
        service_token=settings.PASSENGER_POOL_SERVICE_TOKEN,
    )

    # --- MQTT subscriber ---
    # MQTTSubscriber needs the running loop; we're inside lifespan, so
    # asyncio.get_running_loop() returns the loop the app will run on.
    async def _on_position(topic: str, payload: dict[str, Any]) -> None:
        try:
            position = PositionEvent.model_validate(payload)
        except Exception:
            logger.exception("Invalid position payload on %s", topic)
            return
        await orchestrator.handle_position(position)

    subscriber = MQTTSubscriber(
        loop=asyncio.get_running_loop(),
        topic="gps/+/+/position",
        callback=_on_position,
    )

    # --- Refresh loop: start, await first iteration ---
    stop_event = asyncio.Event()
    first_iteration_done = asyncio.Event()
    refresh_task = asyncio.create_task(
        refresh_loop(
            orchestrator=orchestrator,
            vehicle_map_fetcher=vehicle_map_fetcher,
            pool_fetcher=pool_fetcher,
            settings=settings,
            stop_event=stop_event,
            first_iteration_done=first_iteration_done,
        ),
        name="passenger-service-refresh",
    )

    # Wait for the first fetch to complete before subscribing, so the very
    # first positions aren't dropped as "unknown vehicle". Bounded by a
    # timeout so a broken backend doesn't hang startup — we proceed anyway
    # and let subsequent iterations fill the map in.
    try:
        await asyncio.wait_for(
            first_iteration_done.wait(), timeout=_FIRST_REFRESH_TIMEOUT_S
        )
    except asyncio.TimeoutError:
        logger.warning(
            "First refresh iteration did not complete within %ss; "
            "starting subscriber anyway",
            _FIRST_REFRESH_TIMEOUT_S,
        )

    # --- Subscribe to positions ---
    subscriber.start()

    # --- Expose state for /status ---
    app.state.orchestrator = orchestrator
    app.state.state_store = state_store
    app.state.publisher = publisher
    app.state.subscriber = subscriber
    app.state.route_cache = route_cache
    app.state.vehicle_map_fetcher = vehicle_map_fetcher
    app.state.pool_fetcher = pool_fetcher
    app.state.sequence_client = sequence_client
    app.state.refresh_task = refresh_task
    app.state.refresh_stop_event = stop_event
    app.state.started_at = datetime.now(UTC)

    try:
        yield
    finally:
        # --- Shutdown: stop producers first, then disconnect, then close ---
        stop_event.set()
        try:
            await asyncio.wait_for(refresh_task, timeout=_REFRESH_STOP_TIMEOUT_S)
        except asyncio.TimeoutError:
            logger.warning(
                "Refresh loop did not stop within %ss; cancelling",
                _REFRESH_STOP_TIMEOUT_S,
            )
            refresh_task.cancel()
            try:
                await refresh_task
            except (asyncio.CancelledError, Exception):
                pass

        try:
            subscriber.stop()
        except Exception:
            logger.exception("MQTT subscriber stop failed")
        try:
            publisher.disconnect()
        except Exception:
            logger.exception("MQTT publisher disconnect failed")

        await route_cache.close()
        await vehicle_map_fetcher.close()
        await sequence_client.close()
        await pool_fetcher.close()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Smart Transport — Passenger Service",
        version="0.1.0",
        lifespan=lifespan,
    )

    @app.get("/health")
    async def health() -> dict[str, Any]:
        return {"data": {"status": "ok"}, "meta": None, "error": None}

    @app.get("/status")
    async def status(request: Request) -> dict[str, Any]:
        orch: ArrivalOrchestrator = request.app.state.orchestrator
        store: VehicleStateStore = request.app.state.state_store
        subscriber: MQTTSubscriber = request.app.state.subscriber
        started_at: datetime = request.app.state.started_at

        uptime = (datetime.now(UTC) - started_at).total_seconds()
        return {
            "data": {
                "mqtt_connected": bool(subscriber.subscribed),
                "vehicles_tracked": orch.vehicle_count(),
                "vehicles_with_state": store.size(),
                "events_published": orch.events_published(),
                "uptime_seconds": uptime,
            },
            "meta": None,
            "error": None,
        }

    return app


app = create_app()
