from __future__ import annotations
from datetime import datetime

from pydantic import BaseModel, Field


class GPSPosition(BaseModel):
    vehicle_id: str
    device_id: str

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

    speed: float = Field(default=0.0, ge=0)
    heading: float = Field(default=0.0, ge=0, le=360)

    timestamp: datetime


class VehicleState(BaseModel):
    vehicle_id: str
    device_id: str
    tenant_id: str
    route_id: str
    latitude: float
    longitude: float
    speed: float = 0.0
    heading: float = 0.0
    engine_status: bool = True
    fuel: float = Field(default=100.0, ge=0, le=100)
    last_updated: datetime


class RouteStop(BaseModel):
    stop_id: str

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

    sequence: int = Field(ge=0)
