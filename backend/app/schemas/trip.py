from datetime import datetime
from typing import Literal

from pydantic import Field, computed_field

from app.schemas.base import APIModel

TripStatus = Literal["scheduled", "active", "completed", "cancelled"]
DelayStatus = Literal["delayed", "on_time", "quick"]

# Default number of full route loops a dispatched trip runs before it auto-ends. Used when
# a trip is created without an explicit rounds count (seed data, scripts, API callers that
# omit it), so no journey loops forever by accident.
DEFAULT_JOURNEY_LOOPS = 5

# How many minutes a trip may run over/under its route's planned duration and still count
# as "on time". Beyond this it's flagged "delayed" (late) or "quick" (early). Matches the
# 5-minute threshold used for behind-schedule alerts in alert_service.
ON_TIME_TOLERANCE_MIN = 5


def classify_delay(delay: int) -> DelayStatus:
    """Bucket a signed delay (actual − scheduled minutes) into delayed / on_time / quick."""
    if delay > ON_TIME_TOLERANCE_MIN:
        return "delayed"
    if delay < -ON_TIME_TOLERANCE_MIN:
        return "quick"
    return "on_time"


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
    planned_loops: int = Field(
        default=DEFAULT_JOURNEY_LOOPS,
        gt=0,
        description="How many times the driver runs the route before the journey "
        "auto-ends.",
        json_schema_extra={"example": DEFAULT_JOURNEY_LOOPS},
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
    start_delay: int = Field(default=0, json_schema_extra={"example": 6})
    created_at: datetime = Field(json_schema_extra={"example": "2026-04-08T17:00:00Z"})

    @computed_field
    def delay_status(self) -> DelayStatus:
        """delayed / on_time / quick, derived from the signed running delay + tolerance."""
        return classify_delay(self.delay)

    @computed_field
    def start_delay_status(self) -> DelayStatus:
        """delayed / on_time / quick for the departure, from the signed start delay."""
        return classify_delay(self.start_delay)
