from __future__ import annotations

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from gps_service.config import settings
from gps_service.mqtt.publisher import MQTTPublisher
from gps_service.route_cache.cache import RouteCache
from gps_service.simulator.orchestrator import SimulatorOrchestrator
from gps_service.simulator.state_manager import VehicleStateManager
from gps_service.vehicle_tracker.fetcher import VehicleFetcher
from gps_service.vehicle_tracker.identity import resolve_tenant_id

logger = logging.getLogger(__name__)


def _envelope(data: Any) -> dict[str, Any]:
    return {"data": data, "meta": None, "error": None}


async def _retry(call, *, attempts=10, delay=2.0, what="operation"):
    last_exc = None
    for attempt in range(1, attempts + 1):
        try:
            return await call()
        except Exception as exc:
            last_exc = exc
            logger.warning("%s attempt %d/%d failed: %s", what, attempt, attempts, exc)
            await asyncio.sleep(delay)
    if last_exc is None:
        raise RuntimeError("Retry loop ended without recording an exception")
    raise last_exc


async def _sync_loop(
    orchestrator: SimulatorOrchestrator,
    fetcher: VehicleFetcher,
    interval: float,
    shutdown: asyncio.Event,
) -> None:
    """Periodically re-fetch active vehicles and reconcile state."""
    while not shutdown.is_set():
        try:
            await asyncio.wait_for(shutdown.wait(), timeout=interval)
            return
        except asyncio.TimeoutError:
            pass

        try:
            vehicles = await _retry(
                lambda: fetcher.fetch_active_vehicles(),
                attempts=10,
                delay=2.0,
                what="fetch_active_vehicles",
            )
            orchestrator.sync_vehicles(vehicles)
            logger.info("Reconciled %d active vehicles", len(vehicles))
        except Exception:
            logger.exception("Vehicle refresh failed; keeping current state")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    tenant_id = await _retry(
        lambda: resolve_tenant_id(
            base_url=settings.BACKEND_BASE_URL,
            service_token=settings.BACKEND_SERVICE_TOKEN,
            timeout=settings.BACKEND_REQUEST_TIMEOUT,
        ),
        what="resolve_tenant_id",
    )
    logger.info("Resolved tenant_id=%s", tenant_id)

    publisher = MQTTPublisher()
    publisher.connect()

    route_cache = RouteCache(backend_url=settings.BACKEND_BASE_URL)
    state_manager = VehicleStateManager()

    fetcher = VehicleFetcher(
        tenant_id=tenant_id,
        base_url=settings.BACKEND_BASE_URL,
        service_token=settings.BACKEND_SERVICE_TOKEN,
        page_size=settings.BACKEND_PAGE_SIZE,
        timeout=settings.BACKEND_REQUEST_TIMEOUT,
        device_id_prefix=settings.DEVICE_ID_PREFIX,
    )
    await fetcher.__aenter__()

    try:
        vehicles = await _retry(
            lambda: fetcher.fetch_active_vehicles(),
            attempts=10,
            delay=2.0,
            what="fetch_active_vehicles",
        )
        for vehicle in vehicles:
            state_manager.set(vehicle)
        logger.info("Seeded %d active vehicles", len(vehicles))

        orchestrator = SimulatorOrchestrator(
            state_manager=state_manager,
            route_cache=route_cache,
            publisher=publisher,
            tick_seconds=settings.POLL_INTERVAL,
            backend_token=settings.BACKEND_SERVICE_TOKEN,
        )

        shutdown = asyncio.Event()
        sync_task = asyncio.create_task(
            _sync_loop(
                orchestrator=orchestrator,
                fetcher=fetcher,
                interval=settings.VEHICLE_REFRESH_INTERVAL,
                shutdown=shutdown,
            )
        )
        run_task = asyncio.create_task(orchestrator.run())

        # Stash everything /status and /health need to read.
        app.state.tenant_id = tenant_id
        app.state.publisher = publisher
        app.state.route_cache = route_cache
        app.state.state_manager = state_manager
        app.state.fetcher = fetcher
        app.state.orchestrator = orchestrator
        app.state.shutdown_event = shutdown
        app.state.sync_task = sync_task
        app.state.run_task = run_task
        app.state.started_at = time.monotonic()

        logger.info("GPS simulator started")
        yield
    finally:
        logger.info("Shutdown starting")
        app.state.shutdown_event.set()
        try:
            app.state.orchestrator.stop()
        except Exception:
            logger.exception("Error stopping orchestrator")

        await asyncio.gather(
            app.state.run_task,
            app.state.sync_task,
            return_exceptions=True,
        )

        await fetcher.__aexit__(None, None, None)
        await route_cache.close()
        publisher.disconnect()
        state_manager.save()
        logger.info("Shutdown complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title="GPS Service",
        version="0.1.0",
        lifespan=lifespan,
    )

    @app.get("/health")
    async def health() -> dict[str, Any]:
        return {"status": "ok"}

    @app.get("/status")
    async def status() -> JSONResponse:
        state_manager: VehicleStateManager | None = getattr(
            app.state, "state_manager", None
        )
        publisher: MQTTPublisher | None = getattr(app.state, "publisher", None)
        started_at: float | None = getattr(app.state, "started_at", None)

        active_vehicles = 0
        if state_manager is not None:
            active_vehicles = sum(
                1 for v in state_manager.all() if getattr(v, "status", None) == "active"
            )

        body = _envelope(
            {
                "tenant_id": getattr(app.state, "tenant_id", None),
                "mqtt_connected": bool(publisher and publisher.connected),
                "active_vehicles": active_vehicles,
                "uptime_seconds": (
                    round(time.monotonic() - started_at, 1)
                    if started_at is not None
                    else None
                ),
            }
        )
        return JSONResponse(body)

    return app
