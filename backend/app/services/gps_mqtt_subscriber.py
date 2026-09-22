import json
import logging

from pydantic import ValidationError

from app.core.mqtt_client import MQTTClient
from app.schemas.gps import GPSPositionUpdate

logger = logging.getLogger(__name__)

GPS_POSITION_TOPIC = "gps/+/+/position"


class GPSMQTTSubscriber:
    """Subscribe to MQTT GPS position updates."""

    def __init__(self, mqtt_client: MQTTClient) -> None:
        self.mqtt_client = mqtt_client

    def start(self) -> None:
        """Start listening for GPS position updates."""
        self.mqtt_client.client.on_message = self.on_message
        self.mqtt_client.client.subscribe(GPS_POSITION_TOPIC)

        logger.info("Subscribed to GPS position topic: %s", GPS_POSITION_TOPIC)

    def on_message(self, client, userdata, message) -> None:
        """Process an incoming GPS position message."""
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

        logger.info(
            "Received GPS position for vehicle %s from device %s",
            position.vehicle_id,
            position.device_id,
        )
