from datetime import datetime
from typing import Literal

from pydantic import Field

from app.schemas.base import APIModel


from typing import Optional


EngineStatus = Literal["good", "warning", "critical"]


class GPSPositionUpdate(APIModel):
    """Schema for receiving GPS position updates from external GPS devices/services.

    This schema validates incoming GPS data from the MQTT subscriber.
    The vehicle_id links to a specific vehicle in the system.
    Device authentication is handled separately via MQTT credentials.
    """

    vehicle_id: str = Field(
        description="ID of the vehicle being tracked",
        json_schema_extra={"example": "veh-123"},
    )
    registration_number: Optional[str] = Field(
        default=None,
        description="Vehicle registration number for display/logging",
        json_schema_extra={"example": "RAD 001 A"},
    )
    lat: float = Field(
        description="Latitude coordinate (-90 to 90)",
        ge=-90,
        le=90,
        json_schema_extra={"example": -1.9536},
    )
    lng: float = Field(
        description="Longitude coordinate (-180 to 180)",
        ge=-180,
        le=180,
        json_schema_extra={"example": 30.0606},
    )
    speed: int = Field(
        description="Current speed in km/h",
        ge=0,
        le=200,
        json_schema_extra={"example": 35},
    )
    heading: int = Field(
        description="Direction of travel in degrees (0-359, 0=North)",
        ge=0,
        le=359,
        json_schema_extra={"example": 90},
    )
    fuel: int = Field(
        description="Fuel level as percentage (0-100)",
        ge=0,
        le=100,
        json_schema_extra={"example": 75},
    )
    engine_status: EngineStatus = Field(
        default="good",
        description="Status of the vehicle engine",
        json_schema_extra={"example": "good"},
    )
    timestamp: datetime = Field(
        description="Timestamp when the position was recorded",
        json_schema_extra={"example": "2026-09-18T17:56:15Z"},
    )
    source: Optional[str] = Field(
        default="gps_service",
        description="Source of the GPS data (gps_service, calamp, samsara, etc.)",
        json_schema_extra={"example": "gps_service"},
    )
    device_id: Optional[str] = Field(
        default=None,
        description="ID of the GPS device sending the update",
        json_schema_extra={"example": "gps-sim-001"},
    )
    tenant_id: str = Field(
        description="Tenant ID for multi-tenant isolation",
        json_schema_extra={"example": "tenant-123"},
    )


class GPSPositionResponse(APIModel):
    """Response after successfully processing a GPS position update."""

    vehicle_id: str
    status: str = Field(default="received", json_schema_extra={"example": "received"})
    processed_at: datetime
