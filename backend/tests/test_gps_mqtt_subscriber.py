"""Tests for MQTT GPS position subscriber."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch


class TestGPSMQTTSubscriber:
    """Unit tests for GPSMQTTSubscriber."""

    def test_subscriber_initialization(self):
        """Test subscriber is initialized with MQTT client."""
        mock_mqtt_client = MagicMock()
        from app.services.gps_mqtt_subscriber import GPSMQTTSubscriber

        subscriber = GPSMQTTSubscriber(mock_mqtt_client, loop=MagicMock())
        assert subscriber.mqtt_client == mock_mqtt_client

    def test_subscriber_topic_pattern(self):
        """Test subscriber uses correct topic pattern."""
        from app.services.gps_mqtt_subscriber import GPS_POSITION_TOPIC

        assert GPS_POSITION_TOPIC == "gps/+/+/position"

    @patch("app.services.gps_mqtt_subscriber.GPSPositionUpdate")
    def test_on_message_valid_payload(self, mock_gps_update):
        """Test valid GPS payload is parsed correctly."""
        mock_mqtt_client = MagicMock()
        mock_client = MagicMock()
        mock_mqtt_client.client = mock_client

        from app.services.gps_mqtt_subscriber import GPSMQTTSubscriber

        subscriber = GPSMQTTSubscriber(mock_mqtt_client, loop=MagicMock())

        payload = {
            "vehicle_id": "veh-123",
            "tenant_id": "tenant-1",
            "registration_number": "RAD 001 A",
            "lat": -1.9536,
            "lng": 30.0606,
            "speed": 45,
            "heading": 90,
            "fuel": 85,
            "engine_status": "good",
            "timestamp": "2026-09-24T09:00:00Z",
            "source": "gps_service",
            "device_id": "gps-001",
        }

        mock_message = MagicMock()
        mock_message.topic = "gps/tenant-1/veh-123/position"
        mock_message.payload = json.dumps(payload).encode("utf-8")

        mock_gps_update_instance = MagicMock()
        mock_gps_update_instance.vehicle_id = "veh-123"
        mock_gps_update_instance.device_id = "gps-001"
        mock_gps_update.model_validate.return_value = mock_gps_update_instance

        with patch("app.services.gps_mqtt_subscriber.logger") as mock_logger:
            subscriber.on_message(mock_client, None, mock_message)
            mock_gps_update.model_validate.assert_called_once_with(payload)
            mock_logger.info.assert_called()

    def test_on_message_invalid_json(self):
        """Test invalid JSON payload is logged as error."""
        mock_mqtt_client = MagicMock()
        mock_client = MagicMock()
        mock_mqtt_client.client = mock_client

        from app.services.gps_mqtt_subscriber import GPSMQTTSubscriber

        subscriber = GPSMQTTSubscriber(mock_mqtt_client, loop=MagicMock())

        mock_message = MagicMock()
        mock_message.topic = "gps/tenant-1/veh-123/position"
        mock_message.payload = b"invalid json"

        with patch("app.services.gps_mqtt_subscriber.logger") as mock_logger:
            subscriber.on_message(mock_client, None, mock_message)
            mock_logger.error.assert_called()
            assert "Invalid GPS MQTT payload" in mock_logger.error.call_args[0][0]

    def test_on_message_invalid_schema(self):
        """Test invalid schema payload is logged as error."""
        mock_mqtt_client = MagicMock()
        mock_client = MagicMock()
        mock_mqtt_client.client = mock_client

        from app.services.gps_mqtt_subscriber import GPSMQTTSubscriber

        subscriber = GPSMQTTSubscriber(mock_mqtt_client, loop=MagicMock())

        payload = {"vehicle_id": "veh-123"}

        mock_message = MagicMock()
        mock_message.topic = "gps/tenant-1/veh-123/position"
        mock_message.payload = json.dumps(payload).encode("utf-8")

        from pydantic import ValidationError

        with patch(
            "app.services.gps_mqtt_subscriber.GPSPositionUpdate"
        ) as mock_gps_update:
            mock_gps_update.model_validate.side_effect = (
                ValidationError.from_exception_data(
                    "GPSPositionUpdate",
                    [
                        {
                            "type": "missing",
                            "loc": ("lat",),
                            "msg": "Field required",
                            "input": payload,
                        }
                    ],
                )
            )

            with patch("app.services.gps_mqtt_subscriber.logger") as mock_logger:
                subscriber.on_message(mock_client, None, mock_message)
                mock_logger.error.assert_called()
                assert "validation failed" in mock_logger.error.call_args[0][0].lower()
