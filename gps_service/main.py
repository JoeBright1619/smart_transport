from __future__ import annotations

import asyncio
import logging
import signal

from gps_service.config import settings
from gps_service.mqtt.publisher import MQTTPublisher
from gps_service.route_cache.cache import RouteCache
from gps_service.simulator.orchestrator import SimulatorOrchestrator
from gps_service.simulator.state_manager import VehicleStateManager
from gps_service.vehicle_tracker.fetcher import VehicleFetcher
from gps_service.vehicle_tracker.identity import resolve_tenant_id

logger = logging.getLogger(__name__)


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
            return  # shutdown requested
        except asyncio.TimeoutError:
            pass

        try:
            vehicles = await fetcher.fetch_active_vehicles()
            orchestrator.sync_vehicles(vehicles)
            logger.info("Reconciled %d active vehicles", len(vehicles))
        except Exception:
            logger.exception("Vehicle refresh failed; keeping current state")


async def _run(shutdown: asyncio.Event | None = None) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    tenant_id = await resolve_tenant_id(
        base_url=settings.BACKEND_BASE_URL,
        service_token=settings.BACKEND_SERVICE_TOKEN,
        timeout=settings.BACKEND_REQUEST_TIMEOUT,
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
        vehicles = await fetcher.fetch_active_vehicles()
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

        if shutdown is None:
            shutdown = asyncio.Event()

        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, shutdown.set)
            except NotImplementedError:
                # Windows: add_signal_handler unsupported; best-effort fallback.
                signal.signal(sig, lambda *_: shutdown.set())

        sync_task = asyncio.create_task(
            _sync_loop(
                orchestrator=orchestrator,
                fetcher=fetcher,
                interval=settings.VEHICLE_REFRESH_INTERVAL,
                shutdown=shutdown,
            )
        )
        run_task = asyncio.create_task(orchestrator.run())

        await shutdown.wait()
        logger.info("Shutdown signal received")

        orchestrator.stop()
        await asyncio.gather(run_task, sync_task, return_exceptions=True)

    finally:
        await fetcher.__aexit__(None, None, None)
        await route_cache.close()
        publisher.disconnect()
        state_manager.save()
        logger.info("Shutdown complete")


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
