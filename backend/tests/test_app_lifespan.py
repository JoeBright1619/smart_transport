"""Tests for the backend FastAPI lifespan (Task 7.5).

Guards the invariant that both MQTT subscribers are registered at startup
on the shared paho client. Uses mocks for MQTT, DB, and startup helpers —
the goal is wiring, not behaviour.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI


def _make_fake_engine() -> MagicMock:
    fake_engine = MagicMock()

    fake_connection = MagicMock()
    fake_connection.execute = AsyncMock()

    fake_context_manager = MagicMock()
    fake_context_manager.__aenter__ = AsyncMock(return_value=fake_connection)
    fake_context_manager.__aexit__ = AsyncMock(return_value=None)

    fake_engine.connect.return_value = fake_context_manager
    fake_engine.dispose = AsyncMock()

    return fake_engine


async def _run_lifespan_startup() -> tuple[MagicMock, MagicMock]:
    """Enter and immediately exit the app's lifespan, returning the mocked
    subscriber instances."""

    # Patch modules the lifespan imports.
    fake_engine = _make_fake_engine()

    fake_mqtt_client_instance = MagicMock()
    fake_mqtt_client_instance.connect = MagicMock()
    fake_mqtt_client_instance.disconnect = MagicMock()

    fake_gps_sub = MagicMock()
    fake_gps_sub.start = MagicMock()

    fake_occ_sub = MagicMock()
    fake_occ_sub.start = MagicMock()

    with patch("main.engine", fake_engine), patch(
        "main.MQTTClient", return_value=fake_mqtt_client_instance
    ), patch("main.GPSMQTTSubscriber", return_value=fake_gps_sub), patch(
        "main.OccupancyMQTTSubscriber", return_value=fake_occ_sub
    ), patch("main._warn_if_db_behind_head", new_callable=AsyncMock), patch(
        "main._reconcile_orphaned_trips_on_startup", new_callable=AsyncMock
    ), patch("main.stop_vehicle_simulation", new_callable=AsyncMock):
        from main import lifespan

        app = FastAPI()
        async with lifespan(app):
            pass

    return fake_gps_sub, fake_occ_sub


async def test_lifespan_registers_both_subscribers() -> None:
    gps_sub, occ_sub = await _run_lifespan_startup()
    gps_sub.start.assert_called_once()
    occ_sub.start.assert_called_once()


async def test_lifespan_uses_one_shared_mqtt_client() -> None:
    """Both subscribers must receive the same MQTTClient instance —
    sharing the paho connection is what makes message_callback_add work
    without clobbering on_message."""
    fake_engine = _make_fake_engine()

    with patch("main.engine", fake_engine), patch(
        "main.MQTTClient"
    ) as mock_mqtt_cls, patch("main.GPSMQTTSubscriber") as mock_gps_cls, patch(
        "main.OccupancyMQTTSubscriber"
    ) as mock_occ_cls, patch(
        "main._warn_if_db_behind_head", new_callable=AsyncMock
    ), patch(
        "main._reconcile_orphaned_trips_on_startup", new_callable=AsyncMock
    ), patch("main.stop_vehicle_simulation", new_callable=AsyncMock):
        mock_mqtt = MagicMock()
        mock_mqtt.connect = MagicMock()
        mock_mqtt.disconnect = MagicMock()
        mock_mqtt_cls.return_value = mock_mqtt
        mock_gps_cls.return_value = MagicMock()
        mock_occ_cls.return_value = MagicMock()

        from main import lifespan

        async with lifespan(FastAPI()):
            pass

    # Both subscribers were constructed with the same MQTTClient instance.
    assert mock_gps_cls.call_args.args[0] is mock_mqtt
    assert mock_occ_cls.call_args.args[0] is mock_mqtt
