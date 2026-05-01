from datetime import date, datetime
from typing import Literal

from pydantic import Field

from app.schemas.base import APIModel

MaintenanceType = Literal["routine", "repair", "inspection"]
MaintenanceStatus = Literal["scheduled", "in-progress", "completed"]


class MaintenanceCreate(APIModel):
    vehicle_id: str = Field(json_schema_extra={"example": "veh-uuid"})
    type: MaintenanceType = Field(json_schema_extra={"example": "routine"})
    description: str = Field(
        min_length=1,
        max_length=1000,
        json_schema_extra={"example": "Engine oil change"},
    )
    scheduled_date: date = Field(json_schema_extra={"example": "2026-04-15"})
    cost: float = Field(ge=0, json_schema_extra={"example": 80000})
    next_due: date | None = Field(
        default=None, json_schema_extra={"example": "2026-07-15"}
    )


class MaintenanceUpdate(APIModel):
    status: MaintenanceStatus | None = Field(
        default=None, json_schema_extra={"example": "completed"}
    )
    completed_date: date | None = Field(
        default=None, json_schema_extra={"example": "2026-04-15"}
    )
    cost: float | None = Field(default=None, ge=0, json_schema_extra={"example": 85000})


class MaintenanceRead(APIModel):
    id: str = Field(json_schema_extra={"example": "maint-uuid"})
    vehicle_id: str = Field(json_schema_extra={"example": "veh-uuid"})
    type: MaintenanceType = Field(json_schema_extra={"example": "routine"})
    description: str = Field(json_schema_extra={"example": "Engine oil change"})
    scheduled_date: date = Field(json_schema_extra={"example": "2026-04-15"})
    completed_date: date | None = Field(
        default=None, json_schema_extra={"example": None}
    )
    cost: float = Field(json_schema_extra={"example": 80000})
    status: MaintenanceStatus = Field(json_schema_extra={"example": "scheduled"})
    next_due: date | None = Field(
        default=None, json_schema_extra={"example": "2026-07-15"}
    )
    created_at: datetime = Field(json_schema_extra={"example": "2026-04-08T10:00:00Z"})
