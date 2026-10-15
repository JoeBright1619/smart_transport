from __future__ import annotations

from datetime import UTC, datetime

from gps_service.models.gps_data import VehicleState
from gps_service.mqtt.payload import to_backend_payload, _clamp_int, _wrap_heading


def _vehicle(**overrides) -> VehicleState:
    base = dict(
        vehicle_id="veh-001",
        device_id="sim-veh-001",
        tenant_id="ten-demo-001",
        route_id="route-001",
        latitude=-1.9396,
        longitude=30.0585,
        speed=42.7,
        heading=359.8,
        status="active",
        engine_status="good",
        fuel=78.4,
        last_updated="2026-01-01T00:00:00Z",
    )
    base.update(overrides)
    return VehicleState(**base)


def test_clamp_int_bounds():
    assert _clamp_int(250.0, 0, 200) == 200
    assert _clamp_int(-5.0, 0, 200) == 0
    assert _clamp_int(42.7, 0, 200) == 43
    assert _clamp_int(99.5, 0, 100) == 100


def test_wrap_heading():
    assert _wrap_heading(-5.0) == 355
    assert _wrap_heading(0.0) == 0
    assert _wrap_heading(90.4) == 90
    assert _wrap_heading(359.6) == 0
    assert _wrap_heading(720.0) == 0


def test_payload_uses_backend_field_names():
    ts = datetime(2026, 1, 1, tzinfo=UTC)
    payload = to_backend_payload(_vehicle(), ts)

    assert payload["lat"] == -1.9396
    assert payload["lng"] == 30.0585
    assert "latitude" not in payload
    assert "longitude" not in payload
    assert payload["tenant_id"] == "ten-demo-001"
    assert "tenantId" not in payload


def test_payload_coerces_float_fields_to_int():
    payload = to_backend_payload(
        _vehicle(speed=42.7, fuel=78.4, heading=359.8),
        datetime(2026, 1, 1, tzinfo=UTC),
    )
    assert payload["speed"] == 43
    assert payload["fuel"] == 78
    assert payload["heading"] == 0  # 359.8 rounds to 360, wraps to 0
    assert all(isinstance(payload[f], int) for f in ("speed", "fuel", "heading"))


def test_payload_heading_wraps_for_any_input():
    ts = datetime(2026, 1, 1, tzinfo=UTC)
    for raw, expected in [(-5.0, 355), (0.0, 0), (90.4, 90), (359.6, 0), (720.0, 0)]:
        payload = to_backend_payload(_vehicle(heading=raw), ts)
        assert payload["heading"] == expected, f"heading {raw} → {payload['heading']}"
