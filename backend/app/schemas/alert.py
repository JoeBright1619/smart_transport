from datetime import datetime
from typing import Literal

from pydantic import Field

from app.schemas.base import APIModel

AlertType = Literal[
    "delay", "breakdown", "maintenance", "geofence", "speeding", "info", "capacity"
]
AlertSeverity = Literal["low", "medium", "high", "critical"]


class AlertRead(APIModel):
    id: str = Field(json_schema_extra={"example": "alert-uuid"})
    type: AlertType = Field(json_schema_extra={"example": "delay"})
    severity: AlertSeverity = Field(json_schema_extra={"example": "medium"})
    title: str = Field(json_schema_extra={"example": "Trip Delay: RAD 001 A"})
    message: str = Field(
        json_schema_extra={
            "example": "Vehicle RAD 001 A is 8 minutes behind schedule on Route 101."
        }
    )
    vehicle_id: str | None = Field(
        default=None, json_schema_extra={"example": "veh-uuid"}
    )
    driver_id: str | None = Field(
        default=None, json_schema_extra={"example": "drv-uuid"}
    )
    is_acknowledged: bool = Field(json_schema_extra={"example": False})
    created_at: datetime = Field(json_schema_extra={"example": "2026-04-08T17:01:00Z"})
