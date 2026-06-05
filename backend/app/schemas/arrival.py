from datetime import datetime

from pydantic import Field

from app.schemas.base import APIModel


class ArrivalRead(APIModel):
    vehicle_id: str = Field(json_schema_extra={"example": "veh-uuid"})
    registration_number: str = Field(json_schema_extra={"example": "RAD 001 A"})
    route_id: str = Field(json_schema_extra={"example": "route-uuid"})
    route_name: str = Field(json_schema_extra={"example": "Nyabugogo - Kimironko"})
    distance_to_stop_km: float = Field(json_schema_extra={"example": 2.4})
    current_speed_kmh: int = Field(json_schema_extra={"example": 35})
    eta_minutes: int | None = Field(default=None, json_schema_extra={"example": 4})
    estimated_arrival_time: datetime | None = Field(
        default=None,
        json_schema_extra={"example": "2026-04-08T17:04:00Z"},
    )
    status: str = Field(json_schema_extra={"example": "active"})
    current_occupancy: int = Field(default=0, json_schema_extra={"example": 18})
    seating_capacity: int = Field(default=0, json_schema_extra={"example": 45})
    remaining_seats: int = Field(default=0, json_schema_extra={"example": 27})
