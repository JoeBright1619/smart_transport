"""Periodic refresh of the vehicle map and passenger pool.

Mirrors the *intent* of gps_service's _sync_loop but not its exact
shape. Two departures from gps_service, driven by the different role of
the two services:

- Fetch at t=0, then wait. gps_service waits first — fine there because
  the vehicle map is a producer-side input. For passenger_service, an
  empty map at startup means dropping inbound positions for one
  VEHICLE_REFRESH_INTERVAL; fetching first closes that window.

- Diff the vehicle map here, not inside the orchestrator. The
  orchestrator already exposes set_vehicle_map / release_vehicle, and
  release_vehicle must both drop per-vehicle state and free real
  passenger IDs from _globally_on_board. The loop is the only component
  that sees two consecutive fetches, so the diff belongs here.
"""

from __future__ import annotations

import asyncio
import logging

from passenger_service.config import PassengerServiceSettings
from passenger_service.detection.orchestrator import ArrivalOrchestrator
from passenger_service.passenger_pool.fetcher import PassengerPoolFetcher
from passenger_service.retry import retry
from passenger_service.vehicle_map.fetcher import VehicleMapFetcher

logger = logging.getLogger(__name__)

_RETRY_ATTEMPTS = 10
_RETRY_DELAY = 2.0


async def refresh_loop(
    *,
    orchestrator: ArrivalOrchestrator,
    vehicle_map_fetcher: VehicleMapFetcher,
    pool_fetcher: PassengerPoolFetcher,
    settings: PassengerServiceSettings,
    stop_event: asyncio.Event,
    first_iteration_done: asyncio.Event | None = None,
) -> None:
    """Refresh the vehicle map and passenger pool every interval.

    Terminates promptly when `stop_event` is set (wait_for on the event
    races against the interval, so shutdown is immediate rather than
    delayed by up to one interval). Never raises out of the loop — each
    fetcher's failure is logged and the loop continues; a shutdown or a
    caller-driven exception must be the only reason this exits.

    If ``first_iteration_done`` is provided, it is set exactly once,
    after the first iteration's fetches complete (success or failure).
    Callers use this to gate "start accepting positions" until the map
    has been at least attempted, without waiting a full interval.
    """

    prev_vehicle_ids: set[str] = set()
    interval = settings.VEHICLE_REFRESH_INTERVAL
    first_iteration_done = first_iteration_done  # local for closure

    while not stop_event.is_set():
        # --- Vehicle map ---
        try:
            vehicles = await retry(
                vehicle_map_fetcher.fetch_active_vehicles,
                attempts=_RETRY_ATTEMPTS,
                delay=_RETRY_DELAY,
                what="fetch_active_vehicles",
            )
            new_map = {v.vehicle_id: v for v in vehicles}
            new_ids = set(new_map.keys())
            for gone_id in prev_vehicle_ids - new_ids:
                released = orchestrator.release_vehicle(gone_id)
                if released:
                    logger.info(
                        "Released %d real passenger IDs from vehicle %s",
                        len(released),
                        gone_id,
                    )
            orchestrator.set_vehicle_map(new_map)
            prev_vehicle_ids = new_ids
        except Exception:
            logger.exception("Vehicle map refresh failed; keeping current state")

        # --- Passenger pool ---
        try:
            await retry(
                pool_fetcher.fetch_passenger_ids,
                attempts=_RETRY_ATTEMPTS,
                delay=_RETRY_DELAY,
                what="fetch_passenger_ids",
            )
        except Exception:
            logger.exception("Passenger pool refresh failed; keeping current cache")

        # --- Signal first iteration completion (once) ---
        if first_iteration_done is not None:
            first_iteration_done.set()
            first_iteration_done = None  # no-op on next iteration

        # --- Wait interval or shutdown ---
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval)
            return
        except asyncio.TimeoutError:
            pass
