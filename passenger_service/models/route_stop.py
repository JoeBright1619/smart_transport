from __future__ import annotations

from pydantic import BaseModel, Field


class RouteStop(BaseModel):
    """A single stop on a route, sequence-ordered.

    Mirrors gps_service.models.gps_data.RouteStop by shape. Defined locally
    to keep passenger_service decoupled from gps_service (architectural
    boundary: no imports between services).
    """

    stop_id: str

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

    sequence: int = Field(ge=0)
