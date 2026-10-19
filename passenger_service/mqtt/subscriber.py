import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from concurrent.futures import Future

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

from passenger_service.config import settings

logger = logging.getLogger(__name__)

PositionCallback = Callable[[str, dict], Awaitable[None]]


class MQTTSubscriber:
    """Subscribe to an MQTT topic and dispatch parsed JSON to an async callback.

    Owns its own paho client (distinct client_id from the publisher) so that
    reconnect semantics on the two connections are independent. The callback
    runs on the asyncio loop passed to the constructor, bridged from paho's
    background network thread via ``run_coroutine_threadsafe``.
    """

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        topic: str,
        callback: PositionCallback,
        qos: int = 1,
        broker_url: str = settings.MQTT_BROKER_URL,
        broker_port: int = settings.MQTT_BROKER_PORT,
        username: str = settings.MQTT_USERNAME,
        password: str = settings.MQTT_PASSWORD,
        client_id: str = f"{settings.MQTT_CLIENT_ID}-sub",
    ) -> None:
        self.loop = loop
        self.topic = topic
        self.callback = callback
        self.qos = qos
        self.broker_url = broker_url
        self.broker_port = broker_port

        self.client = mqtt.Client(
            CallbackAPIVersion.VERSION2,
            client_id=client_id,
        )

        if username:
            self.client.username_pw_set(username, password)

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

        self._subscribed = False

    def _on_connect(
        self,
        client: mqtt.Client,
        userdata: object,
        flags: dict,
        reason_code: mqtt.ReasonCode,
        properties: object,
    ) -> None:
        """(Re-)subscribe on every successful connection."""
        if reason_code.is_failure:
            logger.error("MQTT subscriber connect failed: %s", reason_code)
            self._subscribed = False
            return

        result, mid = self.client.subscribe(self.topic, qos=self.qos)

        if result != mqtt.MQTT_ERR_SUCCESS:
            logger.error("Failed to subscribe to %s: rc=%s", self.topic, result)
            self._subscribed = False
            return

        self._subscribed = True
        logger.info("Subscribed to topic: %s (mid=%s)", self.topic, mid)

    def _on_message(
        self,
        client: mqtt.Client,
        userdata: object,
        message: mqtt.MQTTMessage,
    ) -> None:
        """Parse a message and dispatch the callback onto the asyncio loop."""
        try:
            payload = json.loads(message.payload.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            logger.error(
                "Invalid MQTT payload on topic %s: %s",
                message.topic,
                exc,
            )
            return

        future = asyncio.run_coroutine_threadsafe(
            self.callback(message.topic, payload),
            self.loop,
        )

        future.add_done_callback(self._handle_callback_result)

    @staticmethod
    def _handle_callback_result(future: Future[None]) -> None:
        """Surface exceptions raised by the async callback."""
        try:
            future.result()
        except Exception:
            logger.exception("MQTT callback failed")

    def start(self) -> None:
        """Connect to the broker and start the paho network loop."""
        self.client.connect(self.broker_url, self.broker_port)
        self.client.loop_start()

    def stop(self) -> None:
        """Stop the paho network loop and disconnect."""
        self.client.loop_stop()
        self.client.disconnect()
        self._subscribed = False

    @property
    def subscribed(self) -> bool:
        return self._subscribed
