from datetime import datetime

from pydantic import Field

from app.schemas.arrival import PublicArrivalRead
from app.schemas.base import APIModel
from app.schemas.validators import OptionalPhone


class ResolvedRoute(APIModel):
    id: str
    name: str
    number: str
    color: str


class ResolvedStop(APIModel):
    id: str
    name: str


class PassengerProfileRead(APIModel):
    id: str
    user_id: str
    full_name: str
    email: str
    phone: str | None = None
    preferred_routes: list[ResolvedRoute] = Field(default_factory=list)
    preferred_stops: list[ResolvedStop] = Field(default_factory=list)
    notify_on_arrival: bool = True
    notify_on_delay: bool = True
    notification_threshold_minutes: int = 10
    total_trips_recorded: int = 0


class PassengerProfileUpdate(APIModel):
    phone: OptionalPhone = Field(default=None, max_length=50)
    preferred_routes: list[str] | None = None
    preferred_stops: list[str] | None = None
    notify_on_arrival: bool | None = None
    notify_on_delay: bool | None = None
    notification_threshold_minutes: int | None = Field(default=None, ge=1, le=120)


class PassengerListItem(APIModel):
    id: str
    full_name: str
    email: str
    phone: str | None = None
    total_trips_recorded: int = 0
    created_at: datetime


class RouteUsage(APIModel):
    route_id: str
    route_name: str
    trip_count: int


class WeeklyTrips(APIModel):
    week_label: str
    trips: int


class PassengerStatsRead(APIModel):
    total_trips: int
    routes_used: list[RouteUsage] = Field(default_factory=list)
    favourite_stop: str | None = None
    on_time_rate: float = 0.0
    avg_wait_minutes: float = 0.0
    this_week_trips: int = 0
    last_week_trips: int = 0
    weekly_trips: list[WeeklyTrips] = Field(default_factory=list)
    has_enough_data: bool


class PassengerNotification(APIModel):
    stop_name: str
    arrivals: list[PublicArrivalRead]


class TenantContactRead(APIModel):
    id: str
    name: str
    contact_email: str
    phone: str | None = None
    address: str | None = None
    logo_path: str | None = None
