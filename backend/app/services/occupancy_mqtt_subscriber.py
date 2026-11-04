"""Subscribe to MQTT occupancy events published by passenger_service.

Mirrors gps_mqtt_subscriber.py. Differences:

- Topic: gps/+/+/occupancy (not gps/+/+/position).
- Schema: OccupancyEvent (not GPSPositionUpdate).
- Dispatcher: occupancy_service.record(db, event) — validates and
  writes in one transaction. The subscriber commits after the call.

Fire-and-forget dispatch via run_coroutine_threadsafe (same as the GPS
subscriber): paho's on_message runs on its network thread and cannot
await. This means paho considers a message delivered once on_message
returns, even if the async processing later fails. Delivery semantics
are therefore at-most-once at the processing layer — same tradeoff the
GPS path accepts. §8's failure handling (log and drop) covers the
failure modes: validation, DB error, unknown vehicle/tenant.
"""

from __future__ import annotations

import asyncio
import json
import logging
from concurrent.futures import Future

from pydantic import ValidationError

from app.core.database import AsyncSessionLocal
from app.core.mqtt_client import MQTTClient
from app.schemas.occupancy import OccupancyEvent
from app.services.occupancy_service import record
from app.websocket.manager import manager

logger = logging.getLogger(__name__)

OCCUPANCY_TOPIC = "gps/+/+/occupancy"


class OccupancyMQTTSubscriber:
    """Subscribe to MQTT occupancy events and persist them idempotently."""

    def __init__(
        self,
        mqtt_client: MQTTClient,
        loop: asyncio.AbstractEventLoop,
    ) -> None:
        self.mqtt_client = mqtt_client
        self.loop = loop

    def start(self) -> None:
        """Subscribe to the occupancy topic on the shared MQTT client.

        Uses message_callback_add so the GPS subscriber's on_message (the
        paho fallback) is not overwritten. paho routes gps/*/*/occupancy
        messages to this callback and everything else to on_message.
        """
        self.mqtt_client.client.message_callback_add(OCCUPANCY_TOPIC, self.on_message)

        result, mid = self.mqtt_client.client.subscribe(OCCUPANCY_TOPIC)

        if result != 0:
            raise RuntimeError(f"Failed to subscribe to {OCCUPANCY_TOPIC}: rc={result}")

        logger.info(
            "Subscribed to occupancy topic: %s (mid=%s)",
            OCCUPANCY_TOPIC,
            mid,
        )

    def on_message(self, client, userdata, message) -> None:
        """Validate an inbound occupancy message and dispatch to the processor."""
        logger.info("Received occupancy MQTT message: topic=%s", message.topic)

        try:
            payload = json.loads(message.payload.decode("utf-8"))
            event = OccupancyEvent.model_validate(payload)

        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            logger.error(
                "Invalid occupancy MQTT payload on topic %s: %s",
                message.topic,
                exc,
            )
            return

        except ValidationError as exc:
            logger.error(
                "Occupancy validation failed on topic %s: %s",
                message.topic,
                exc,
            )
            return

        future = asyncio.run_coroutine_threadsafe(
            self._process_occupancy(event),
            self.loop,
        )
        future.add_done_callback(self._handle_processing_result)
        logger.info(
            "PROCESSING OCCUPANCY: vehicle=%s key=%s",
            event.vehicle_id,
            event.idempotency_key,
        )

    async def _process_occupancy(self, event: OccupancyEvent) -> None:
        """Persist a validated occupancy event and broadcast if newly inserted."""
        async with AsyncSessionLocal() as db:
            result = await record(db, event)
            await db.commit()
            logger.info(
                "OCCUPANCY COMMITTED: vehicle=%s key=%s inserted=%s",
                event.vehicle_id,
                event.idempotency_key,
                result.inserted,
            )

        # Broadcast only on insert — duplicates are invisible to clients.
        # After commit, so clients never see an uncommitted occupancy.
        if result.inserted:
            remaining_seats = (
                max(0, result.seating_capacity - event.onboard)
                if result.seating_capacity is not None
                else None
            )
            await manager.publish_to_tenant(
                event.tenant_id,
                {
                    "type": "vehicle_occupancy_updated",
                    "vehicleId": event.vehicle_id,
                    "currentOccupancy": event.onboard,
                    "seatingCapacity": result.seating_capacity,
                    "remainingSeats": remaining_seats,
                },
            )

    @staticmethod
    def _handle_processing_result(future: Future[None]) -> None:
        """Log exceptions raised by the async processor (§8: log/drop)."""
        try:
            future.result()
        except Exception:
            logger.exception("Failed to process occupancy event")
