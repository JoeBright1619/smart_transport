import json
import time
from typing import Any

import paho.mqtt.client as mqtt
from paho.mqtt.reasoncodes import ReasonCode
from paho.mqtt.properties import Properties
from paho.mqtt.enums import CallbackAPIVersion

from gps_service.config import settings


class MQTTPublisher:
    def __init__(
        self,
        broker_url: str = settings.MQTT_BROKER_URL,
        broker_port: int = settings.MQTT_BROKER_PORT,
        username: str = settings.MQTT_USERNAME,
        password: str = settings.MQTT_PASSWORD,
        client_id: str = settings.MQTT_CLIENT_ID,
        retry_attempts: int = settings.MQTT_RETRY_ATTEMPTS,
        retry_delay: float = settings.MQTT_RETRY_DELAY,
    ) -> None:
        self.broker_url = broker_url
        self.broker_port = broker_port
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay

        self.client = mqtt.Client(
            CallbackAPIVersion.VERSION2,
            client_id=client_id,
        )

        if username:
            self.client.username_pw_set(username, password)

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

        self._connected = False

    def _on_connect(
        self,
        client: mqtt.Client,
        userdata: Any,
        flags: dict[str, Any],
        reason_code: ReasonCode,
        properties: Properties | None,
    ) -> None:
        if reason_code == 0:
            self._connected = True
        else:
            self._connected = False

    def _on_disconnect(
        self,
        client: mqtt.Client,
        userdata: Any,
        flags: mqtt.DisconnectFlags,
        reason_code: ReasonCode,
        properties: Properties | None,
    ) -> None:
        self._connected = False

    def connect(self) -> None:
        for attempt in range(self.retry_attempts):
            try:
                self.client.connect(self.broker_url, self.broker_port)
                self.client.loop_start()

                if self.client.is_connected():
                    return

            except Exception:
                if attempt == self.retry_attempts - 1:
                    raise

            delay = self.retry_delay * (2**attempt)
            time.sleep(delay)

        raise ConnectionError("Unable to connect to MQTT broker")

    def disconnect(self) -> None:
        self.client.loop_stop()
        self.client.disconnect()
        self._connected = False

    def publish(
        self,
        topic: str,
        payload: dict[str, Any],
        qos: int = 1,
        retain: bool = False,
    ) -> None:
        if qos not in (0, 1, 2):
            raise ValueError("QoS must be 0, 1, or 2")

        if not self.client.is_connected():
            self.connect()

        message = json.dumps(payload)

        result = self.client.publish(
            topic,
            payload=message,
            qos=qos,
            retain=retain,
        )

        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            raise RuntimeError(f"MQTT publish failed with return code {result.rc}")
