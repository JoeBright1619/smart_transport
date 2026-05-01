from datetime import datetime
from typing import Literal

from pydantic import Field

from app.schemas.base import APIModel

TripStatus = Literal["scheduled", "active", "completed", "cancelled"]


class TripCreate(APIModel):
    vehicle_id: str = Field(json_schema_extra={"example": "veh-uuid"})
    route_id: str = Field(json_schema_extra={"example": "route-uuid"})
    driver_id: str = Field(json_schema_extra={"example": "drv-uuid"})
    scheduled_start: datetime = Field(
        json_schema_extra={"example": "2026-04-09T08:00:00Z"}
    )
    scheduled_end: datetime = Field(
        json_schema_extra={"example": "2026-04-09T08:35:00Z"}
    )


class TripUpdate(APIModel):
    status: TripStatus = Field(json_schema_extra={"example": "active"})


class TripRead(APIModel):
    id: str = Field(json_schema_extra={"example": "trip-uuid"})
    vehicle_id: str = Field(json_schema_extra={"example": "veh-uuid"})
    route_id: str = Field(json_schema_extra={"example": "route-uuid"})
    driver_id: str = Field(json_schema_extra={"example": "drv-uuid"})
    scheduled_start: datetime = Field(
        json_schema_extra={"example": "2026-04-09T08:00:00Z"}
    )
    actual_start: datetime | None = Field(
        default=None, json_schema_extra={"example": "2026-04-09T08:03:00Z"}
    )
    scheduled_end: datetime = Field(
        json_schema_extra={"example": "2026-04-09T08:35:00Z"}
    )
    actual_end: datetime | None = Field(
        default=None, json_schema_extra={"example": None}
    )
    status: TripStatus = Field(json_schema_extra={"example": "active"})
    passengers: int = Field(json_schema_extra={"example": 34})
    delay: int = Field(json_schema_extra={"example": 3})
    created_at: datetime = Field(json_schema_extra={"example": "2026-04-08T17:00:00Z"})
