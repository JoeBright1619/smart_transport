from datetime import date, datetime
from typing import Literal

from pydantic import Field

from app.schemas.base import APIModel

DriverStatus = Literal["available", "on-trip", "off-duty"]


class DriverCreate(APIModel):
    name: str = Field(
        min_length=1, max_length=255, json_schema_extra={"example": "Eric Nsabimana"}
    )
    license_number: str = Field(
        min_length=1, max_length=50, json_schema_extra={"example": "DL-RW-0003"}
    )
    phone: str = Field(
        min_length=1, max_length=50, json_schema_extra={"example": "+250788345678"}
    )
    certification_expiry: date = Field(json_schema_extra={"example": "2027-12-31"})


class DriverUpdate(APIModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        json_schema_extra={"example": "Eric Nsabimana"},
    )
    phone: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
        json_schema_extra={"example": "+250788999000"},
    )
    status: DriverStatus | None = Field(
        default=None, json_schema_extra={"example": "off-duty"}
    )
    vehicle_id: str | None = Field(
        default=None, json_schema_extra={"example": "veh-uuid"}
    )
    certification_expiry: date | None = Field(
        default=None, json_schema_extra={"example": "2028-01-01"}
    )


class DriverRead(APIModel):
    id: str = Field(json_schema_extra={"example": "drv-uuid"})
    name: str = Field(json_schema_extra={"example": "Patrick Hakizimana"})
    license_number: str = Field(json_schema_extra={"example": "DL-RW-0001"})
    phone: str = Field(json_schema_extra={"example": "+250788111222"})
    rating: float = Field(json_schema_extra={"example": 4.7})
    total_trips: int = Field(json_schema_extra={"example": 143})
    status: DriverStatus = Field(json_schema_extra={"example": "available"})
    vehicle_id: str | None = Field(default=None, json_schema_extra={"example": None})
    certification_expiry: date = Field(json_schema_extra={"example": "2027-06-30"})
    created_at: datetime = Field(json_schema_extra={"example": "2026-04-01T08:00:00Z"})
