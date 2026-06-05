from datetime import datetime

from pydantic import Field

from app.schemas.base import APIModel


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
    total_trips_recorded: int = 0


class PassengerProfileUpdate(APIModel):
    phone: str | None = Field(default=None, max_length=50)
    preferred_routes: list[str] | None = None
    preferred_stops: list[str] | None = None
    notify_on_arrival: bool | None = None
    notify_on_delay: bool | None = None


class PassengerListItem(APIModel):
    id: str
    full_name: str
    email: str
    phone: str | None = None
    total_trips_recorded: int = 0
    created_at: datetime
