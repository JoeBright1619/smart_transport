"""Inbound MQTT position event published by gps_service.

Wire contract is owned by ``gps_service/mqtt/payload.py``
(``to_backend_payload``), which mirrors the backend's ``GPSPositionUpdate``
schema. The wire field names are snake_case and match the design's internal
names, so this model uses no aliases. The wire carries five extra fields
(``device_id``, ``heading``, ``fuel``, ``engine_status``, ``source``) that
``PositionEvent`` does not carry; they are silently ignored on parse.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PositionEvent(BaseModel):
    """Parsed inbound position event from gps_service."""

    model_config = ConfigDict(extra="ignore")

    # wire field: vehicle_id
    vehicle_id: str = Field(description="Backend vehicle ID")
    # wire field: tenant_id
    tenant_id: str = Field(description="Tenant for multi-tenant isolation")
    # wire field: lat
    lat: float = Field(ge=-90, le=90, description="Latitude in degrees")
    # wire field: lng
    lng: float = Field(ge=-180, le=180, description="Longitude in degrees")
    # wire field: speed
    speed: float = Field(ge=0, description="Ground speed")
    # wire field: timestamp
    timestamp: datetime = Field(description="Position fix time (ISO 8601)")
