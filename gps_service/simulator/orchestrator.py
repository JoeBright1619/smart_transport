from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime

from gps_service.models.gps_data import GPSPosition, VehicleState
from gps_service.mqtt.publisher import MQTTPublisher
from gps_service.route_cache.cache import RouteCache
from gps_service.simulator.engine import SimulationEngine
from gps_service.simulator.state_manager import VehicleStateManager

logger = logging.getLogger(__name__)

TICK_SECONDS = 5
MQTT_MAX_RETRIES = 3
MQTT_RETRY_DELAY_SECONDS = 1.0


class SimulatorOrchestrator:
    """Coordinate vehicle simulation, route data, state, and MQTT publishing."""

    def __init__(
        self,
        state_manager: VehicleStateManager,
        route_cache: RouteCache,
        publisher: MQTTPublisher,
        engine: SimulationEngine | None = None,
        tick_seconds: float = TICK_SECONDS,
        backend_token: str | None = None,
    ) -> None:
        self.state_manager = state_manager
        self.route_cache = route_cache
        self.publisher = publisher
        self.engine = engine or SimulationEngine()
        self.tick_seconds = tick_seconds
        self.backend_token = backend_token

        self._running = False

    async def run(self) -> None:
        """Run the simulator until stopped."""

        self._running = True

        logger.info("GPS simulator started")

        try:
            while self._running:
                tick_started = asyncio.get_running_loop().time()

                await self.tick()

                elapsed = asyncio.get_running_loop().time() - tick_started
                sleep_seconds = max(0.0, self.tick_seconds - elapsed)

                await asyncio.sleep(sleep_seconds)
        finally:
            self._running = False
            logger.info("GPS simulator stopped")

    def stop(self) -> None:
        """Stop the simulator after the current tick."""

        self._running = False

    async def tick(self) -> None:
        """Advance and publish all active vehicles once."""

        vehicles = self.state_manager.all()

        for vehicle in vehicles:
            if vehicle.status != "active":
                continue

            try:
                await self._process_vehicle(vehicle.vehicle_id)
            except Exception:
                logger.exception(
                    "Failed to process vehicle %s",
                    vehicle.vehicle_id,
                )

        self.state_manager.save()

    async def _process_vehicle(self, vehicle_id: str) -> None:
        """Advance and publish one vehicle."""

        vehicle = self.state_manager.get(vehicle_id)

        if vehicle is None:
            return

        try:
            stops = await self.route_cache.get_route_stops(
                vehicle.route_id,
                self.backend_token,
            )
        except Exception:
            logger.exception(
                "Failed to fetch route %s for vehicle %s",
                vehicle.route_id,
                vehicle_id,
            )
            return

        if len(stops) < 2:
            logger.warning(
                "Vehicle %s has insufficient route stops",
                vehicle_id,
            )
            return

        simulation_state = self.state_manager.get_simulation_state(
            vehicle_id,
        )

        updated_vehicle = self.engine.advance_vehicle(
            vehicle,
            stops,
            simulation_state,
        )

        if updated_vehicle is None:
            return

        now = datetime.now(UTC)

        updated_vehicle.last_updated = now

        self.state_manager.set(updated_vehicle)

        position = GPSPosition(
            vehicle_id=updated_vehicle.vehicle_id,
            device_id=updated_vehicle.device_id,
            latitude=updated_vehicle.latitude,
            longitude=updated_vehicle.longitude,
            speed=updated_vehicle.speed,
            heading=updated_vehicle.heading,
            timestamp=now,
        )
        topic = (
            f"gps/{updated_vehicle.tenant_id}/" f"{updated_vehicle.vehicle_id}/position"
        )
        await self._publish_with_retry(
            topic=topic,
            payload=position.model_dump(mode="json"),
        )
        logger.debug(
            "Published position for %s: lat=%.5f lng=%.5f speed=%.1f heading=%.1f",
            position.vehicle_id,
            position.latitude,
            position.longitude,
            position.speed,
            position.heading,
        )

    async def _publish_with_retry(
        self,
        topic: str,
        payload: dict,
    ) -> None:
        for attempt in range(1, MQTT_MAX_RETRIES + 1):
            try:
                self.publisher.publish(
                    topic=topic,
                    payload=payload,
                    qos=1,
                )

                return
            except Exception:
                if attempt == MQTT_MAX_RETRIES:
                    logger.exception(
                        "MQTT publish failed after %s attempts: %s",
                        MQTT_MAX_RETRIES,
                        topic,
                    )
                    raise

                logger.warning(
                    "MQTT publish failed for %s " "(attempt %s/%s), retrying",
                    topic,
                    attempt,
                    MQTT_MAX_RETRIES,
                )

                await asyncio.sleep(MQTT_RETRY_DELAY_SECONDS)

    def sync_vehicles(self, vehicles: list[VehicleState]) -> None:
        """Reconcile the state manager against a fresh vehicle list.

        Adds vehicles that are new, removes vehicles that disappeared.
        Existing vehicles are left untouched (their simulation state must
        survive across refreshes).
        """
        incoming = {v.vehicle_id: v for v in vehicles}
        existing = {v.vehicle_id for v in self.state_manager.all()}

        for vehicle_id, vehicle in incoming.items():
            if vehicle_id not in existing:
                self.state_manager.set(vehicle)

        for vehicle_id in existing - incoming.keys():
            self.state_manager.remove(vehicle_id)
