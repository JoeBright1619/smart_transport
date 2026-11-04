"""Tests for OccupancyMQTTSubscriber.

Covers: valid message dispatch, JSON decode failure drop, schema
validation failure drop, and the async processor's transaction
(commit called after record). Uses mocks — no broker, no DB.
"""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.occupancy_mqtt_subscriber import (
    OCCUPANCY_TOPIC,
    OccupancyMQTTSubscriber,
)


def _paho_message(topic: str, payload: dict) -> MagicMock:
    """Minimal paho MQTTMessage stand-in: .topic and .payload."""
    msg = MagicMock()
    msg.topic = topic
    msg.payload = json.dumps(payload).encode("utf-8")
    return msg


def _valid_event() -> dict:
    return {
        "vehicle_id": "veh-1",
        "tenant_id": "ten-1",
        "stop_id": "stop-1",
        "route_id": "route-1",
        "onboard": 10,
        "boardings": 2,
        "alightings": 1,
        "arrival_sequence": 3,
        "position_timestamp": "2026-01-01T00:00:00+00:00",
        "service_timestamp": "2026-01-01T00:00:00+00:00",
        "idempotency_key": "veh-1:stop-1:3",
        "boarded_passenger_ids": [],
        "alighted_passenger_ids": [],
        "revenue_delta": 0.0,
    }


def _make() -> tuple[OccupancyMQTTSubscriber, MagicMock, MagicMock]:
    mqtt_client = MagicMock()
    mqtt_client.client = MagicMock()
    mqtt_client.client.subscribe.return_value = (0, 123)
    loop = MagicMock(spec=asyncio.AbstractEventLoop)
    sub = OccupancyMQTTSubscriber(mqtt_client=mqtt_client, loop=loop)
    return sub, mqtt_client, loop


class TestOccupancyMQTTSubscriber:
    def test_start_subscribes_to_occupancy_topic(self) -> None:
        sub, mqtt_client, _ = _make()
        sub.start()
        mqtt_client.client.subscribe.assert_called_once_with(OCCUPANCY_TOPIC)
        mqtt_client.client.message_callback_add.assert_called_once_with(
            OCCUPANCY_TOPIC, sub.on_message
        )

    def test_start_raises_on_subscribe_failure(self) -> None:
        sub, mqtt_client, _ = _make()
        mqtt_client.client.subscribe.return_value = (1, 0)
        with pytest.raises(RuntimeError, match="Failed to subscribe"):
            sub.start()

    def test_on_message_invalid_json_dropped(self) -> None:
        sub, _, loop = _make()
        msg = MagicMock()
        msg.topic = "gps/ten-1/veh-1/occupancy"
        msg.payload = b"not-json"

        with patch(
            "app.services.occupancy_mqtt_subscriber.asyncio.run_coroutine_threadsafe"
        ) as rct:
            sub.on_message(None, None, msg)

        rct.assert_not_called()

    def test_on_message_validation_failure_dropped(self) -> None:
        sub, _, _ = _make()
        msg = _paho_message(
            "gps/ten-1/veh-1/occupancy",
            {"vehicle_id": "veh-1"},  # missing required fields
        )

        with patch(
            "app.services.occupancy_mqtt_subscriber.asyncio.run_coroutine_threadsafe"
        ) as rct:
            sub.on_message(None, None, msg)

        rct.assert_not_called()

    def test_on_message_valid_dispatches_coroutine(self) -> None:
        sub, _, loop = _make()
        msg = _paho_message("gps/ten-1/veh-1/occupancy", _valid_event())

        future = MagicMock()
        future.add_done_callback = MagicMock()

        with patch(
            "app.services.occupancy_mqtt_subscriber.asyncio.run_coroutine_threadsafe",
            return_value=future,
        ) as rct:
            sub.on_message(None, None, msg)

        rct.assert_called_once()
        # First positional arg is the coroutine; second is the loop.
        coro_arg, loop_arg = rct.call_args.args
        assert loop_arg is loop
        # Coroutine's name/qualname reflect _process_occupancy.
        assert "process_occupancy" in getattr(coro_arg, "__qualname__", "")
        future.add_done_callback.assert_called_once()


class TestProcessOccupancy:
    async def test_process_commits_after_record(self) -> None:
        """_process_occupancy opens a session, calls record, commits."""
        sub, _, _ = _make()
        _paho_message("gps/ten-1/veh-1/occupancy", _valid_event())

        # Reconstruct the validated event exactly as on_message would.
        from app.schemas.occupancy import OccupancyEvent

        event = OccupancyEvent.model_validate(_valid_event())

        # Fake the session context manager.
        fake_session = AsyncMock()
        fake_session.__aenter__ = AsyncMock(return_value=fake_session)
        fake_session.__aexit__ = AsyncMock(return_value=None)
        fake_session.commit = AsyncMock()

        fake_factory = MagicMock(return_value=fake_session)

        with patch(
            "app.services.occupancy_mqtt_subscriber.AsyncSessionLocal",
            fake_factory,
        ), patch(
            "app.services.occupancy_mqtt_subscriber.record",
            new_callable=AsyncMock,
        ) as mock_record:
            await sub._process_occupancy(event)

        mock_record.assert_awaited_once()
        # The event passed through unchanged.
        assert mock_record.call_args.args[1].idempotency_key == "veh-1:stop-1:3"
        fake_session.commit.assert_awaited_once()

    async def test_process_propagates_record_errors(self) -> None:
        """record() raising is not swallowed here; the done-callback handles it."""
        sub, _, _ = _make()

        from app.schemas.occupancy import OccupancyEvent

        event = OccupancyEvent.model_validate(_valid_event())

        fake_session = AsyncMock()
        fake_session.__aenter__ = AsyncMock(return_value=fake_session)
        fake_session.__aexit__ = AsyncMock(return_value=None)
        fake_session.commit = AsyncMock()

        with patch(
            "app.services.occupancy_mqtt_subscriber.AsyncSessionLocal",
            MagicMock(return_value=fake_session),
        ), patch(
            "app.services.occupancy_mqtt_subscriber.record",
            new_callable=AsyncMock,
            side_effect=RuntimeError("db down"),
        ):
            with pytest.raises(RuntimeError, match="db down"):
                await sub._process_occupancy(event)

        fake_session.commit.assert_not_awaited()
