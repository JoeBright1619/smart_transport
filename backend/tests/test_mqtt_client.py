"""Tests for MQTT client wrapper."""

from __future__ import annotations

from unittest.mock import patch

import pytest


class TestMQTTClient:
    """Unit tests for MQTTClient wrapper."""

    @patch("app.core.mqtt_client.mqtt.Client")
    def test_mqtt_client_initialization(self, mock_mqtt_client):
        """Test MQTT client is initialized with correct settings."""
        with patch("app.core.mqtt_client.settings") as mock_settings:
            mock_settings.MQTT_BROKER_URL = "localhost"
            mock_settings.MQTT_BROKER_PORT = 1883
            mock_settings.MQTT_CLIENT_ID = "test-client"
            mock_settings.MQTT_USERNAME = None
            mock_settings.MQTT_PASSWORD = None

            from app.core.mqtt_client import MQTTClient

            client = MQTTClient()

            assert client.broker_host == "localhost"
            assert client.broker_port == 1883
            assert client.client_id == "test-client"
            mock_mqtt_client.assert_called_once_with(client_id="test-client")

    @patch("app.core.mqtt_client.mqtt.Client")
    def test_mqtt_client_with_credentials(self, mock_mqtt_client):
        """Test MQTT client is configured with username and password."""
        with patch("app.core.mqtt_client.settings") as mock_settings:
            mock_settings.MQTT_BROKER_URL = "localhost"
            mock_settings.MQTT_BROKER_PORT = 1883
            mock_settings.MQTT_CLIENT_ID = "test-client"
            mock_settings.MQTT_USERNAME = "testuser"
            mock_settings.MQTT_PASSWORD = "testpass"

            from app.core.mqtt_client import MQTTClient

            client = MQTTClient()
            client.client.username_pw_set.assert_called_once_with(
                "testuser", "testpass"
            )

    @patch("app.core.mqtt_client.mqtt.Client")
    def test_mqtt_connect(self, mock_mqtt_client):
        """Test connect method starts the MQTT loop."""
        with patch("app.core.mqtt_client.settings") as mock_settings:
            mock_settings.MQTT_BROKER_URL = "localhost"
            mock_settings.MQTT_BROKER_PORT = 1883
            mock_settings.MQTT_CLIENT_ID = "test-client"
            mock_settings.MQTT_USERNAME = None
            mock_settings.MQTT_PASSWORD = None

            from app.core.mqtt_client import MQTTClient

            client = MQTTClient()
            mock_instance = mock_mqtt_client.return_value

            client.connect()

            mock_instance.connect.assert_called_once_with("localhost", 1883)
            mock_instance.loop_start.assert_called_once()

    @patch("app.core.mqtt_client.mqtt.Client")
    def test_mqtt_disconnect(self, mock_mqtt_client):
        """Test disconnect method stops the MQTT loop."""
        with patch("app.core.mqtt_client.settings") as mock_settings:
            mock_settings.MQTT_BROKER_URL = "localhost"
            mock_settings.MQTT_BROKER_PORT = 1883
            mock_settings.MQTT_CLIENT_ID = "test-client"
            mock_settings.MQTT_USERNAME = None
            mock_settings.MQTT_PASSWORD = None

            from app.core.mqtt_client import MQTTClient

            client = MQTTClient()
            mock_instance = mock_mqtt_client.return_value

            client.disconnect()

            mock_instance.loop_stop.assert_called_once()
            mock_instance.disconnect.assert_called_once()


class TestMQTTClientConnection:
    """Tests for MQTT connection handling."""

    @patch("app.core.mqtt_client.mqtt.Client")
    def test_connection_failure_handling(self, mock_mqtt_client):
        """Test that connection failures are handled gracefully."""
        with patch("app.core.mqtt_client.settings") as mock_settings:
            mock_settings.MQTT_BROKER_URL = "invalid-host"
            mock_settings.MQTT_BROKER_PORT = 1883
            mock_settings.MQTT_CLIENT_ID = "test-client"
            mock_settings.MQTT_USERNAME = None
            mock_settings.MQTT_PASSWORD = None

            mock_instance = mock_mqtt_client.return_value
            mock_instance.connect.side_effect = Exception("Connection refused")

            from app.core.mqtt_client import MQTTClient

            client = MQTTClient()

            # Should raise the exception
            with pytest.raises(Exception, match="Connection refused"):
                client.connect()
