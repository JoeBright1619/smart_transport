import asyncio
import json
import logging

from pydantic import ValidationError

from app.core.database import AsyncSessionLocal
from app.core.mqtt_client import MQTTClient
from app.schemas.gps import GPSPositionUpdate
from app.services.gps_handler import process_gps_update
from concurrent.futures import Future

logger = logging.getLogger(__name__)

GPS_POSITION_TOPIC = "gps/+/+/position"


class GPSMQTTSubscriber:
    """Subscribe to MQTT GPS position updates."""

    def __init__(
        self,
        mqtt_client: MQTTClient,
        loop: asyncio.AbstractEventLoop,
    ) -> None:
        self.mqtt_client = mqtt_client
        self.loop = loop

    def start(self) -> None:
        """Start listening for GPS position updates."""
        self.mqtt_client.client.on_message = self.on_message

        result, mid = self.mqtt_client.client.subscribe(GPS_POSITION_TOPIC)

        if result != 0:
            raise RuntimeError(
                f"Failed to subscribe to {GPS_POSITION_TOPIC}: rc={result}"
            )

        logger.info(
            "Subscribed to GPS position topic: %s (mid=%s)",
            GPS_POSITION_TOPIC,
            mid,
        )

    def on_message(self, client, userdata, message) -> None:
        """Validate an incoming MQTT message and hand it to the async processor."""
        logger.info("Received GPS MQTT message: topic=%s", message.topic)

        try:
            payload = json.loads(message.payload.decode("utf-8"))
            position = GPSPositionUpdate.model_validate(payload)

        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            logger.error(
                "Invalid GPS MQTT payload on topic %s: %s",
                message.topic,
                exc,
            )
            return

        except ValidationError as exc:
            logger.error(
                "GPS position validation failed on topic %s: %s",
                message.topic,
                exc,
            )
            return

        future = asyncio.run_coroutine_threadsafe(
            self._process_position(position),
            self.loop,
        )

        future.add_done_callback(self._handle_processing_result)
        logger.info("PROCESSING GPS UPDATE: %s", position.vehicle_id)

    async def _process_position(
        self,
        position: GPSPositionUpdate,
    ) -> None:
        """Process a validated GPS update using an async database session."""
        async with AsyncSessionLocal() as db:
            result = await process_gps_update(db, position)
            logger.info("GPS HANDLER RESULT: %s", result)
            await db.commit()
            logger.info("GPS UPDATE COMMITTED")

    @staticmethod
    def _handle_processing_result(
        future: Future[None],
    ) -> None:
        """Log exceptions from asynchronous GPS processing."""
        try:
            future.result()
        except Exception:
            logger.exception("Failed to process GPS position update")
