"""Unit tests for MQTTSubscriber (mocked paho client, no broker)."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import MagicMock

import paho.mqtt.client as mqtt
import pytest

from passenger_service.mqtt.subscriber import MQTTSubscriber


@pytest.fixture
def mock_client_cls(mocker):
    return mocker.patch("passenger_service.mqtt.subscriber.mqtt.Client")


@pytest.fixture
def loop():
    """A real event loop the subscriber can dispatch to."""
    return asyncio.new_event_loop()


@pytest.fixture
def callback():
    return MagicMock()


@pytest.fixture
def subscriber(mock_client_cls, loop, callback):
    return MQTTSubscriber(
        loop=loop,
        topic="gps/+/+/position",
        callback=callback,
        qos=1,
    )


def _ok_reason_code():
    rc = MagicMock()
    rc.is_failure = False
    return rc


def _fail_reason_code():
    rc = MagicMock()
    rc.is_failure = True
    return rc


def _make_message(topic: str, payload: dict | bytes) -> MagicMock:
    msg = MagicMock()
    msg.topic = topic
    raw = payload if isinstance(payload, bytes) else json.dumps(payload).encode("utf-8")
    msg.payload = raw
    return msg


# ---- construction --------------------------------------------------------


def test_uses_distinct_client_id_from_publisher(subscriber, mock_client_cls):
    """Client is constructed with client_id ending in '-sub'."""
    call_kwargs = mock_client_cls.call_args.kwargs
    assert call_kwargs["client_id"].endswith("-sub")


def test_does_not_set_username_when_blank(mock_client_cls, loop, callback):
    sub = MQTTSubscriber(
        loop=loop,
        topic="t",
        callback=callback,
        username="",
        password="",
    )
    assert not sub.client.username_pw_set.called


def test_sets_username_when_present(mock_client_cls, loop, callback):
    MQTTSubscriber(
        loop=loop,
        topic="t",
        callback=callback,
        username="u",
        password="p",
    )
    mock_client_cls.return_value.username_pw_set.assert_called_once_with("u", "p")


# ---- start / stop --------------------------------------------------------


def test_start_connects_and_starts_loop(subscriber, mock_client_cls):
    subscriber.start()
    subscriber.client.connect.assert_called_once_with(
        subscriber.broker_url, subscriber.broker_port
    )
    subscriber.client.loop_start.assert_called_once()


def test_stop_stops_loop_and_disconnects(subscriber):
    subscriber.stop()
    subscriber.client.loop_stop.assert_called_once()
    subscriber.client.disconnect.assert_called_once()
    assert subscriber.subscribed is False


# ---- subscribe on connect ------------------------------------------------


def test_subscribes_on_successful_connect(subscriber):
    subscriber.client.subscribe.return_value = (mqtt.MQTT_ERR_SUCCESS, 42)

    subscriber._on_connect(
        subscriber.client,
        None,
        {},
        _ok_reason_code(),
        None,
    )

    subscriber.client.subscribe.assert_called_once_with("gps/+/+/position", qos=1)
    assert subscriber.subscribed is True


def test_does_not_subscribe_on_failed_connect(subscriber):
    subscriber._on_connect(
        subscriber.client,
        None,
        {},
        _fail_reason_code(),
        None,
    )
    assert not subscriber.client.subscribe.called
    assert subscriber.subscribed is False


def test_subscribe_failure_leaves_not_subscribed(subscriber):
    subscriber.client.subscribe.return_value = (mqtt.MQTT_ERR_NO_CONN, 0)

    subscriber._on_connect(
        subscriber.client,
        None,
        {},
        _ok_reason_code(),
        None,
    )
    assert subscriber.subscribed is False


# ---- on_message ----------------------------------------------------------


def test_on_message_dispatches_callback_with_topic_and_payload(
    subscriber, loop, callback
):
    """A valid message schedules the callback with the parsed dict."""
    received = []

    async def record(topic, payload):
        received.append((topic, payload))

    subscriber.callback = record

    msg = _make_message("gps/tenant-1/veh-123/position", {"vehicle_id": "veh-123"})

    subscriber._on_message(subscriber.client, None, msg)

    # run_coroutine_threadsafe schedules on the loop; drive it synchronously.
    loop.run_until_complete(asyncio.sleep(0.05))

    assert received == [("gps/tenant-1/veh-123/position", {"vehicle_id": "veh-123"})]


def test_on_message_drops_invalid_json(subscriber, mocker, callback):
    """Invalid UTF-8/JSON is logged and does not invoke the callback."""
    log = mocker.patch("passenger_service.mqtt.subscriber.logger")

    msg = _make_message("gps/x/y/position", b"not json")

    subscriber._on_message(subscriber.client, None, msg)

    callback.assert_not_called()
    log.error.assert_called_once()
    assert "Invalid MQTT payload" in log.error.call_args[0][0]


def test_on_message_drops_non_utf8(subscriber, mocker, callback):
    log = mocker.patch("passenger_service.mqtt.subscriber.logger")

    msg = _make_message("gps/x/y/position", b"\xff\xfe")

    subscriber._on_message(subscriber.client, None, msg)

    callback.assert_not_called()
    log.error.assert_called_once()


def test_async_callback_exception_is_logged(subscriber, loop, mocker):
    """Exception raised inside the async callback is logged via done-callback."""
    log = mocker.patch("passenger_service.mqtt.subscriber.logger")

    async def boom(topic, payload):
        raise RuntimeError("kaboom")

    subscriber.callback = boom

    msg = _make_message("gps/x/y/position", {"a": 1})
    subscriber._on_message(subscriber.client, None, msg)

    loop.run_until_complete(asyncio.sleep(0.05))

    assert log.exception.called
    assert "MQTT callback failed" in log.exception.call_args[0][0]
