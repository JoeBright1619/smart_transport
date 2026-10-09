from __future__ import annotations
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

EngineStatus = Literal["good", "warning", "critical"]
VehicleStatus = Literal["active", "idle", "maintenance", "offline"]


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

    # Operational state from the backend. Drives whether the simulator
    # advances this vehicle on a tick.
    status: VehicleStatus = "active"

    # Engine health from the backend. Metadata only; the simulator does
    # not modify it and does not use it to gate movement.
    engine_status: EngineStatus = "good"

    fuel: float = Field(default=100.0, ge=0, le=100)
    last_updated: datetime


class RouteStop(BaseModel):
    stop_id: str

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

    sequence: int = Field(ge=0)
