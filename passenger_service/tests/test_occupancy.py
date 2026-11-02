"""Unit tests for OccupancyEvent and build_occupancy_event."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from passenger_service.models.occupancy import OccupancyEvent, build_occupancy_event


def _valid_kwargs(**overrides) -> dict:
    """Baseline kwargs for build_occupancy_event, with selective overrides."""
    base = {
        "vehicle_id": "veh-123",
        "tenant_id": "ten-demo-001",
        "stop_id": "stop-42",
        "route_id": "route-7",
        "onboard": 15,
        "boardings": 3,
        "alightings": 2,
        "arrival_sequence": 5,
        "position_timestamp": "2026-10-19T14:00:00+00:00",
        "boarded_passenger_ids": ["pas-a", "pas-b"],
        "alighted_passenger_ids": ["pas-c"],
        "revenue_delta": 120.0,
    }
    base.update(overrides)
    return base


# ---- build_occupancy_event ----------------------------------------------


def test_build_fills_derived_fields():
    """Helper computes service_timestamp, source, and idempotency_key."""
    before = datetime.now().astimezone()
    event = build_occupancy_event(**_valid_kwargs())
    after = datetime.now().astimezone()

    assert event.source == "passenger_service"
    assert event.idempotency_key == "veh-123:stop-42:5"

    # service_timestamp parses as ISO 8601 and lies within [before, after].
    parsed = datetime.fromisoformat(event.service_timestamp)
    assert before <= parsed <= after


def test_build_passes_through_caller_fields():
    """All non-derived fields are forwarded verbatim."""
    event = build_occupancy_event(**_valid_kwargs())

    assert event.vehicle_id == "veh-123"
    assert event.tenant_id == "ten-demo-001"
    assert event.stop_id == "stop-42"
    assert event.route_id == "route-7"
    assert event.onboard == 15
    assert event.boardings == 3
    assert event.alightings == 2
    assert event.arrival_sequence == 5
    assert event.position_timestamp == "2026-10-19T14:00:00+00:00"
    assert event.boarded_passenger_ids == ["pas-a", "pas-b"]
    assert event.alighted_passenger_ids == ["pas-c"]
    assert event.revenue_delta == 120.0


def test_idempotency_key_format():
    """Key is exactly '{vehicle_id}:{stop_id}:{arrival_sequence}'."""
    event = build_occupancy_event(
        **_valid_kwargs(
            vehicle_id="veh-abc",
            stop_id="stop-xyz",
            arrival_sequence=42,
        )
    )
    assert event.idempotency_key == "veh-abc:stop-xyz:42"


def test_service_timestamp_is_iso8601_parseable():
    """service_timestamp round-trips through datetime.fromisoformat."""
    event = build_occupancy_event(**_valid_kwargs())
    parsed = datetime.fromisoformat(event.service_timestamp)
    assert parsed.tzinfo is not None


# ---- field validation ---------------------------------------------------


@pytest.mark.parametrize(
    "field, value",
    [
        ("onboard", -1),
        ("boardings", -1),
        ("alightings", -1),
        ("arrival_sequence", -1),
    ],
)
def test_negative_counts_rejected(field, value):
    """ge=0 constraint on onboard/boardings/alightings/arrival_sequence."""
    with pytest.raises(ValidationError):
        OccupancyEvent(
            **{
                **_valid_kwargs(),
                field: value,
                "service_timestamp": "2026-10-19T14:00:01+00:00",
                "source": "passenger_service",
                "idempotency_key": "veh-123:stop-42:5",
            }
        )


def test_required_fields_missing_raises():
    """Omitting a required field raises ValidationError."""
    with pytest.raises(ValidationError):
        OccupancyEvent(
            vehicle_id="veh-123",
            tenant_id="ten",
            stop_id="stop",
            route_id="route",
            onboard=0,
            boardings=0,
            alightings=0,
            arrival_sequence=0,
            # position_timestamp omitted
            service_timestamp="2026-10-19T14:00:00+00:00",
            source="passenger_service",
            idempotency_key="veh-123:stop:0",
        )


def test_source_defaults_to_passenger_service():
    """Direct construction (bypassing helper) uses source default."""
    event = OccupancyEvent(
        vehicle_id="v",
        tenant_id="t",
        stop_id="s",
        route_id="r",
        onboard=0,
        boardings=0,
        alightings=0,
        arrival_sequence=0,
        position_timestamp="2026-10-19T14:00:00+00:00",
        service_timestamp="2026-10-19T14:00:01+00:00",
        idempotency_key="v:s:0",
    )
    assert event.source == "passenger_service"


# ---- serialisation ------------------------------------------------------


def test_model_dump_json_round_trip():
    """model_dump_json produces a string that parses back to equal data."""
    event = build_occupancy_event(**_valid_kwargs())
    json_str = event.model_dump_json()
    restored = OccupancyEvent.model_validate_json(json_str)
    assert restored == event


def test_model_dump_shape_matches_schema():
    """All schema fields appear in model_dump."""
    expected = {
        "vehicle_id",
        "tenant_id",
        "stop_id",
        "route_id",
        "onboard",
        "boardings",
        "alightings",
        "arrival_sequence",
        "position_timestamp",
        "service_timestamp",
        "source",
        "idempotency_key",
        "boarded_passenger_ids",
        "alighted_passenger_ids",
        "revenue_delta",
    }
    assert set(build_occupancy_event(**_valid_kwargs()).model_dump().keys()) == expected


def test_revenue_delta_zero_default_when_omitted() -> None:
    kwargs = _valid_kwargs()
    del kwargs["revenue_delta"]
    event = build_occupancy_event(**kwargs)
    assert event.revenue_delta == 0.0


def test_revenue_delta_rejects_negative() -> None:
    with pytest.raises(ValidationError):
        OccupancyEvent(
            **{
                **_valid_kwargs(),
                "revenue_delta": -1.0,
                "service_timestamp": "2026-10-19T14:00:01+00:00",
                "source": "passenger_service",
                "idempotency_key": "veh-123:stop-42:5",
            }
        )


def test_boarded_and_alighted_ids_default_to_empty() -> None:
    kwargs = _valid_kwargs()
    del kwargs["boarded_passenger_ids"]
    del kwargs["alighted_passenger_ids"]
    event = build_occupancy_event(**kwargs)
    assert event.boarded_passenger_ids == []
    assert event.alighted_passenger_ids == []
