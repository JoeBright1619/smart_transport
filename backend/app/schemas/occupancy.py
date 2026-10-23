"""Inbound occupancy event schema, published by passenger_service over MQTT.

Authored against design §5, not against ``passenger_service/models/occupancy.py``
(Task 4.4 is behind §5; Task 4.5 will bring the wire model into line). The
backend validates against this schema on ingestion and hands off to
``app.services.occupancy_writer`` for persistence.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class OccupancyEvent(BaseModel):
    """Wire format for occupancy events published to MQTT."""

    model_config = ConfigDict(extra="ignore")

    vehicle_id: str
    tenant_id: str
    stop_id: str
    route_id: str
    onboard: int = Field(ge=0)
    boardings: int = Field(ge=0)
    alightings: int = Field(ge=0)
    arrival_sequence: int = Field(ge=0)
    position_timestamp: str
    service_timestamp: str
    source: str = "passenger_service"
    idempotency_key: str

    # Per-passenger attribution (§7). Empty and absent are equivalent.
    boarded_passenger_ids: list[str] = Field(default_factory=list)
    alighted_passenger_ids: list[str] = Field(default_factory=list)

    # Revenue in simulation units. 0.0 when no alightings generated revenue.
    revenue_delta: float = Field(default=0.0, ge=0.0)
