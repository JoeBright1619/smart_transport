from datetime import datetime

from app.schemas.base import APIModel


class BoardingRecordRead(APIModel):
    id: str
    trip_id: str | None
    stop_id: str
    stop_name: str
    passenger_id: str | None
    event_type: str
    count: int
    recorded_at: datetime
    occupancy_after: int
    tenant_id: str


class PassengerTripRead(APIModel):
    boarding_id: str
    event_type: str
    count: int
    stop_id: str
    stop_name: str
    trip_id: str | None
    recorded_at: datetime
    occupancy_after: int
