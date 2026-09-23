import os

import paho.mqtt.client as mqtt


class MQTTClient:
    """MQTT client wrapper for the Smart Transport backend."""

    def __init__(self) -> None:
        self.broker_host = os.getenv("MQTT_BROKER_HOST", "localhost")
        self.broker_port = int(os.getenv("MQTT_BROKER_PORT", "1883"))
        self.client_id = os.getenv("MQTT_CLIENT_ID", "smart-transport-backend")

        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=self.client_id,
        )

    def connect(self) -> None:
        """Connect to the configured MQTT broker."""
        self.client.connect(self.broker_host, self.broker_port)
        self.client.loop_start()

    def disconnect(self) -> None:
        """Disconnect from the MQTT broker."""
        self.client.loop_stop()
        self.client.disconnect()
