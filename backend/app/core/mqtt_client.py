from app.core.config import settings

import paho.mqtt.client as mqtt
import logging


logger = logging.getLogger(__name__)


class MQTTClient:
    """MQTT client wrapper for the Smart Transport backend"""

    def __init__(self) -> None:
        self.broker_host = settings.MQTT_BROKER_URL
        self.broker_port = settings.MQTT_BROKER_PORT
        self.client_id = settings.MQTT_CLIENT_ID

        self.client = mqtt.Client(client_id=self.client_id)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

        if settings.MQTT_USERNAME:
            self.client.username_pw_set(
                settings.MQTT_USERNAME,
                settings.MQTT_PASSWORD or "",
            )

    def connect(self) -> None:
        """Connect to the configured MQTT broker."""
        self.client.connect(self.broker_host, self.broker_port)
        self.client.loop_start()

    def disconnect(self) -> None:
        """Disconnect from the MQTT broker."""
        self.client.loop_stop()
        self.client.disconnect()

    def _on_connect(
        self, client, userdata, flags, reason_code, properties=None
    ) -> None:
        if reason_code == 0:
            logger.info("MQTT connected successfully")
        else:
            logger.error(
                "MQTT connection failed: reason_code=%s",
                reason_code,
            )

    def _on_disconnect(
        self,
        client,
        userdata,
        disconnect_flags,
        reason_code,
        properties=None,
    ) -> None:
        logger.warning(f"MQTT disconnected: reason_code={reason_code}")
