from datetime import datetime

from pydantic import Field

from app.schemas.base import APIModel


class SuperadminTenantRead(APIModel):
    id: str = Field(json_schema_extra={"example": "ten-uuid"})
    name: str = Field(json_schema_extra={"example": "EcoFleet Ltd"})
    contact_email: str = Field(json_schema_extra={"example": "admin@ecofleet.rw"})
    is_active: bool = Field(json_schema_extra={"example": True})
    vehicle_count: int = Field(json_schema_extra={"example": 12})
    user_count: int = Field(json_schema_extra={"example": 8})
    created_at: datetime = Field(json_schema_extra={"example": "2026-03-01T08:00:00Z"})


class SuperadminTenantDetail(SuperadminTenantRead):
    updated_at: datetime = Field(json_schema_extra={"example": "2026-04-01T10:00:00Z"})


class SuperadminTenantUpdate(APIModel):
    is_active: bool | None = Field(default=None, json_schema_extra={"example": False})


class ImpersonationResponse(APIModel):
    access_token: str = Field(json_schema_extra={"example": "<1hr_impersonation_jwt>"})


class PlatformAnalytics(APIModel):
    total_tenants: int = Field(json_schema_extra={"example": 12})
    active_tenants: int = Field(json_schema_extra={"example": 11})
    total_vehicles: int = Field(json_schema_extra={"example": 187})
    total_trips_today: int = Field(json_schema_extra={"example": 432})
    total_passengers_today: int = Field(json_schema_extra={"example": 17280})
