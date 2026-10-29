from __future__ import annotations

from pydantic import BaseModel, Field


class VehicleInfo(BaseModel):
    """The vehicle subset the passenger simulation needs.

    Populated from backend.app.schemas.vehicle.VehicleRead on the wire.
    tenant_id is populated from VehicleRead.tenantId, added to the read
    schema specifically for this consumer.
    """

    vehicle_id: str
    tenant_id: str
    route_id: str
    seating_capacity: int = Field(ge=0)
    current_occupancy: int = Field(ge=0)
