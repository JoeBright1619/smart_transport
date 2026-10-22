"""Unit tests for the inbound PositionEvent model."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from passenger_service.models.position import PositionEvent


# Realistic wire payload as produced by gps_service/mqtt/payload.py
# (to_backend_payload). Includes the five fields PositionEvent ignores.
WIRE_PAYLOAD = {
    "vehicle_id": "veh-001",
    "device_id": "dev-001",
    "tenant_id": "tenant-a",
    "lat": 51.5074,
    "lng": -0.1278,
    "speed": 42,
    "heading": 90,
    "fuel": 75,
    "engine_status": "running",
    "timestamp": "2026-10-22T12:34:56+00:00",
    "source": "gps_service",
}


def test_parses_representative_payload() -> None:
    event = PositionEvent.model_validate(WIRE_PAYLOAD)

    # Assert on a subset so a typo in one field's mapping is caught
    # independently of the others.
    assert event.vehicle_id == "veh-001"
    assert event.lat == 51.5074
    assert event.speed == 42.0


def test_parses_speed_as_int_from_wire() -> None:
    event = PositionEvent.model_validate(WIRE_PAYLOAD)
    # Wire emits speed as int (gps_service clamps via _clamp_int);
    # the model exposes it as float.
    assert isinstance(event.speed, float)
    assert event.speed == 42.0


def test_timestamp_parsed_as_datetime() -> None:
    event = PositionEvent.model_validate(WIRE_PAYLOAD)
    assert event.timestamp == datetime(2026, 10, 22, 12, 34, 56, tzinfo=UTC)


def test_rejects_malformed_payload_missing_vehicle_id() -> None:
    payload = dict(WIRE_PAYLOAD)
    payload.pop("vehicle_id")
    with pytest.raises(ValidationError):
        PositionEvent.model_validate(payload)


def test_rejects_out_of_range_lat() -> None:
    payload = {**WIRE_PAYLOAD, "lat": 91.0}
    with pytest.raises(ValidationError):
        PositionEvent.model_validate(payload)


def test_rejects_out_of_range_lng() -> None:
    payload = {**WIRE_PAYLOAD, "lng": -181.0}
    with pytest.raises(ValidationError):
        PositionEvent.model_validate(payload)


def test_rejects_negative_speed() -> None:
    payload = {**WIRE_PAYLOAD, "speed": -1}
    with pytest.raises(ValidationError):
        PositionEvent.model_validate(payload)


def test_extra_fields_ignored() -> None:
    # WIRE_PAYLOAD contains device_id, heading, fuel, engine_status, source —
    # all beyond the six fields in the design. Parsing must not raise, and the
    # model must not expose them.
    event = PositionEvent.model_validate(WIRE_PAYLOAD)
    dumped = event.model_dump()
    assert set(dumped) == {
        "vehicle_id",
        "tenant_id",
        "lat",
        "lng",
        "speed",
        "timestamp",
    }
