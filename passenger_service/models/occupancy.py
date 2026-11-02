"""Wire format for occupancy events published to MQTT."""

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class OccupancyEvent(BaseModel):
    """Wire format for occupancy events published to MQTT.

    Emitted by passenger_service once per detected stop arrival. Consumed by
    the backend's occupancy MQTT subscriber, which validates against a mirrored
    schema and writes it to ``boarding_records``.
    """

    vehicle_id: str = Field(description="Backend vehicle ID")
    tenant_id: str = Field(description="Tenant for multi-tenant isolation")
    stop_id: str = Field(description="Stop where the arrival was detected")
    route_id: str = Field(description="Route the vehicle is currently on")
    onboard: int = Field(ge=0, description="Total passengers after this stop")
    boardings: int = Field(ge=0, description="Passengers who boarded at this stop")
    alightings: int = Field(ge=0, description="Passengers who alighted at this stop")
    arrival_sequence: int = Field(
        ge=0, description="Monotonic per-vehicle arrival counter"
    )
    position_timestamp: str = Field(
        description="ISO 8601 — from the triggering position event"
    )
    service_timestamp: str = Field(
        description="ISO 8601 — when passenger_service emitted this"
    )
    source: str = Field(
        default="passenger_service", description="Fixed string for provenance"
    )
    idempotency_key: str = Field(
        description=(
            '"{vehicle_id}:{stop_id}:{arrival_sequence}" — note that '
            "arrival_sequence is the per-vehicle monotonic counter, not the "
            "stop's route sequence. Stable across replays (backend dedups "
            "on ON CONFLICT)."
        )
    )

    # Per-passenger attribution (§7). Populated from SimulationResult;
    # empty lists are equivalent to "no real passengers" and are accepted
    # by the backend (Task 2.1 schema has the same defaults).
    boarded_passenger_ids: list[str] = Field(
        default_factory=list,
        description="Real user IDs that boarded at this stop",
    )
    alighted_passenger_ids: list[str] = Field(
        default_factory=list,
        description="Real user IDs that alighted at this stop",
    )

    # Simulation revenue for this stop. 0.0 when no alightings generated
    # revenue. Units are simulation-only (REVENUE_PER_KM is a demo constant).
    revenue_delta: float = Field(
        default=0.0,
        ge=0.0,
        description="Revenue delta from alightings, simulation units",
    )


def build_occupancy_event(
    *,
    vehicle_id: str,
    tenant_id: str,
    stop_id: str,
    route_id: str,
    onboard: int,
    boardings: int,
    alightings: int,
    arrival_sequence: int,
    position_timestamp: str,
    boarded_passenger_ids: list[str] | None = None,
    alighted_passenger_ids: list[str] | None = None,
    revenue_delta: float | None = None,
) -> OccupancyEvent:
    """Construct an ``OccupancyEvent`` with derived fields filled in.

    ``service_timestamp``, ``source``, and ``idempotency_key`` are computed
    here so the caller only has to provide the values it already has.

    ``boarded_passenger_ids`` / ``alighted_passenger_ids`` / ``revenue_delta``
    are the three §5 fields added when this model was reconciled with the
    backend schema. ``None`` maps to empty/0.0 (matching the backend's
    defaults); the orchestrator (Task 4.6) always passes real values.
    """
    return OccupancyEvent(
        vehicle_id=vehicle_id,
        tenant_id=tenant_id,
        stop_id=stop_id,
        route_id=route_id,
        onboard=onboard,
        boardings=boardings,
        alightings=alightings,
        arrival_sequence=arrival_sequence,
        position_timestamp=position_timestamp,
        service_timestamp=datetime.now(UTC).isoformat(),
        source="passenger_service",
        idempotency_key=f"{vehicle_id}:{stop_id}:{arrival_sequence}",
        boarded_passenger_ids=boarded_passenger_ids or [],
        alighted_passenger_ids=alighted_passenger_ids or [],
        revenue_delta=revenue_delta if revenue_delta is not None else 0.0,
    )
