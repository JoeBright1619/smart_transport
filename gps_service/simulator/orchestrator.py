from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime

from gps_service.models.gps_data import GPSPosition
from gps_service.mqtt.publisher import MQTTPublisher
from gps_service.route_cache.cache import RouteCache
from gps_service.simulator.engine import SimulationEngine
from gps_service.simulator.state_manager import VehicleStateManager

logger = logging.getLogger(__name__)

TICK_SECONDS = 5


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
            if not vehicle.engine_status:
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

        stops = await self.route_cache.get_route_stops(
            vehicle.route_id,
            self.backend_token,
        )

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
        self.publisher.publish(
            topic=topic,
            payload=position.model_dump(mode="json"),
            qos=1,
        )
