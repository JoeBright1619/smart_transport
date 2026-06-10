from datetime import datetime
from typing import Literal

from pydantic import Field, computed_field

from app.schemas.base import APIModel

VehicleStatus = Literal["active", "idle", "maintenance", "offline"]
EngineStatus = Literal["good", "warning", "critical"]
OccupancyStatus = Literal["available", "nearly_full", "full"]


class Location(APIModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class VehicleCreate(APIModel):
    registration_number: str = Field(
        min_length=1, max_length=50, json_schema_extra={"example": "RAD 007 G"}
    )
    model: str = Field(
        min_length=1, max_length=100, json_schema_extra={"example": "Yutong ZK6120"}
    )
    seating_capacity: int = Field(default=45, gt=0, json_schema_extra={"example": 45})
    status: VehicleStatus = Field(default="idle", json_schema_extra={"example": "idle"})


class VehicleUpdate(APIModel):
    status: VehicleStatus | None = Field(
        default=None, json_schema_extra={"example": "maintenance"}
    )
    fuel: int | None = Field(
        default=None, ge=0, le=100, json_schema_extra={"example": 45}
    )
    seating_capacity: int | None = Field(
        default=None, gt=0, json_schema_extra={"example": 45}
    )
    route_id: str | None = Field(
        default=None, json_schema_extra={"example": "route-uuid"}
    )
    driver_id: str | None = Field(
        default=None, json_schema_extra={"example": "drv-uuid"}
    )


class VehicleRead(APIModel):
    id: str = Field(json_schema_extra={"example": "veh-uuid"})
    registration_number: str = Field(json_schema_extra={"example": "RAD 001 A"})
    model: str = Field(json_schema_extra={"example": "Yutong ZK6120"})
    seating_capacity: int = Field(default=45, json_schema_extra={"example": 45})
    current_occupancy: int = Field(default=0, json_schema_extra={"example": 18})
    status: VehicleStatus = Field(json_schema_extra={"example": "active"})
    speed: int | None = Field(default=None, json_schema_extra={"example": 35})
    heading: int | None = Field(default=None, json_schema_extra={"example": 90})
    fuel: int | None = Field(default=None, json_schema_extra={"example": 75})
    engine_status: EngineStatus = Field(json_schema_extra={"example": "good"})
    route_id: str | None = Field(
        default=None, json_schema_extra={"example": "route-uuid"}
    )
    driver_id: str | None = Field(
        default=None, json_schema_extra={"example": "drv-uuid"}
    )
    updated_at: datetime = Field(
        serialization_alias="lastUpdate",
        json_schema_extra={"example": "2026-04-08T17:00:00Z"},
    )

    lat: float | None = Field(default=None, exclude=True)
    lng: float | None = Field(default=None, exclude=True)

    @computed_field
    def current_location(self) -> Location | None:
        if self.lat is not None and self.lng is not None:
            return Location(lat=self.lat, lng=self.lng)
        return None

    @computed_field
    def remaining_seats(self) -> int:
        return max(0, self.seating_capacity - self.current_occupancy)


class VehicleOccupancyRead(APIModel):
    vehicle_id: str = Field(json_schema_extra={"example": "veh-uuid"})
    seating_capacity: int = Field(json_schema_extra={"example": 45})
    current_occupancy: int = Field(json_schema_extra={"example": 38})
    remaining_seats: int = Field(json_schema_extra={"example": 7})
    status: OccupancyStatus = Field(json_schema_extra={"example": "nearly_full"})
