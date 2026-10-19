"""Unit tests for MQTTPublisher (mocked paho client, no broker)."""

from types import SimpleNamespace

import paho.mqtt.client as mqtt
import pytest

from passenger_service.mqtt.publisher import MQTTPublisher


def _rc(code: int) -> SimpleNamespace:
    """Stand-in for paho's MQTTMessageInfo (only .rc is used)."""
    return SimpleNamespace(rc=code)


@pytest.fixture
def mock_client_cls(mocker):
    """Patch mqtt.Client; return the patched class (use .return_value for instance)."""
    return mocker.patch("passenger_service.mqtt.publisher.mqtt.Client")


@pytest.fixture
def mock_sleep(mocker):
    """Patch time.sleep so retries don't actually wait."""
    return mocker.patch("passenger_service.mqtt.publisher.time.sleep")


@pytest.fixture
def publisher(mock_client_cls, mock_sleep):
    """A publisher whose underlying paho client is a MagicMock."""
    pub = MQTTPublisher(retry_attempts=3, retry_delay=0.01)
    # Default: connected, so publish() doesn't try to (re)connect unless a test
    # explicitly sets is_connected.return_value = False.
    mock_client_cls.return_value.is_connected.return_value = True
    return pub


def test_connect_calls_client_connect_and_loop_start(
    publisher, mock_client_cls, mock_sleep
):
    """connect() invokes paho's connect + loop_start and waits for is_connected."""
    client = mock_client_cls.return_value
    client.is_connected.side_effect = [False, True]

    publisher.connect()

    client.connect.assert_called_once_with(publisher.broker_url, publisher.broker_port)
    client.loop_start.assert_called_once()


def test_connect_retries_and_raises_after_exhaustion(
    publisher, mock_client_cls, mock_sleep
):
    """connect() retries retry_attempts times, then raises ConnectionError."""
    client = mock_client_cls.return_value
    client.connect.side_effect = OSError("boom")

    with pytest.raises(ConnectionError):
        publisher.connect()

    assert client.connect.call_count == publisher.retry_attempts


def test_publish_encodes_json_and_passes_qos_retain(publisher, mock_client_cls):
    """publish() JSON-encodes the payload and forwards qos/retain verbatim."""
    client = mock_client_cls.return_value
    client.publish.return_value = _rc(mqtt.MQTT_ERR_SUCCESS)

    publisher.publish("gps/t/v/occupancy", {"onboard": 7}, qos=1, retain=True)

    client.publish.assert_called_once_with(
        "gps/t/v/occupancy",
        payload='{"onboard": 7}',
        qos=1,
        retain=True,
    )


def test_publish_rejects_invalid_qos(publisher):
    """QoS outside {0,1,2} raises ValueError before any I/O."""
    with pytest.raises(ValueError):
        publisher.publish("t", {}, qos=3)


def test_publish_reconnects_when_disconnected(publisher, mock_client_cls, mock_sleep):
    """If the client is disconnected, publish() calls connect() first."""
    client = mock_client_cls.return_value
    # connect() loops on is_connected; let it succeed on the first check.
    client.is_connected.side_effect = [False, True]
    client.publish.return_value = _rc(mqtt.MQTT_ERR_SUCCESS)

    publisher.publish("t", {"a": 1})

    client.connect.assert_called_once()
    client.publish.assert_called_once()


def test_publish_retries_then_succeeds(publisher, mock_client_cls, mock_sleep):
    """Transient publish failure is retried; success on the 3rd attempt returns cleanly."""
    client = mock_client_cls.return_value
    client.publish.side_effect = [
        _rc(mqtt.MQTT_ERR_NO_CONN),
        _rc(mqtt.MQTT_ERR_NO_CONN),
        _rc(mqtt.MQTT_ERR_SUCCESS),
    ]

    publisher.publish("t", {"a": 1})

    assert client.publish.call_count == 3
    # Backoff: retry_delay * 2^(attempt-1) → 0.01*1 + 0.01*2 = 0.03s of sleep total.
    assert mock_sleep.call_count == 2


def test_publish_raises_after_all_retries_fail(publisher, mock_client_cls, mock_sleep):
    """After retry_attempts failures, RuntimeError is raised with the last rc."""
    client = mock_client_cls.return_value
    client.publish.return_value = _rc(mqtt.MQTT_ERR_NO_CONN)

    with pytest.raises(RuntimeError, match="return code 4"):
        publisher.publish("t", {"a": 1})

    assert client.publish.call_count == publisher.retry_attempts
    # Sleeps between attempts only — one fewer than attempt count.
    assert mock_sleep.call_count == publisher.retry_attempts - 1


def test_disconnect_stops_loop_and_disconnects(publisher, mock_client_cls):
    """disconnect() calls loop_stop + disconnect."""
    client = mock_client_cls.return_value

    publisher.disconnect()

    client.loop_stop.assert_called_once()
    client.disconnect.assert_called_once()
