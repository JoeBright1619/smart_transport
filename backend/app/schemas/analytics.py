from datetime import date as date_type
from datetime import datetime
from typing import List, Literal, Optional, Union

from pydantic import Field

from app.schemas.base import APIModel


class AnalyticsSummary(APIModel):
    total_trips: int = Field(json_schema_extra={"example": 148}, alias="totalTrips")
    on_time_percentage: float = Field(
        json_schema_extra={"example": 91.2}, alias="onTimePercentage"
    )
    avg_delay: float = Field(json_schema_extra={"example": 3.3}, alias="avgDelay")
    total_passengers: int = Field(
        json_schema_extra={"example": 5920}, alias="totalPassengers"
    )
    total_revenue: float = Field(
        json_schema_extra={"example": 2960000}, alias="totalRevenue"
    )
    total_fuel_consumption: float = Field(
        json_schema_extra={"example": 850}, alias="totalFuelConsumption"
    )


class AnalyticsDaily(APIModel):
    date: date_type = Field(json_schema_extra={"example": "2026-04-01"})
    total_trips: int = Field(json_schema_extra={"example": 21}, alias="totalTrips")
    on_time_percentage: float = Field(
        json_schema_extra={"example": 90.0}, alias="onTimePercentage"
    )
    avg_delay: float = Field(json_schema_extra={"example": 3.5}, alias="avgDelay")
    total_passengers: int = Field(
        json_schema_extra={"example": 840}, alias="totalPassengers"
    )
    fuel_consumption: float = Field(
        json_schema_extra={"example": 122}, alias="fuelConsumption"
    )
    revenue: float = Field(json_schema_extra={"example": 420000}, alias="revenue")


class AnalyticsResponseData(APIModel):
    summary: AnalyticsSummary
    daily: list[AnalyticsDaily]


class RouteReportData(APIModel):
    route_id: str
    route_name: str
    on_time_rate: float
    avg_trip_duration_minutes: float
    total_passengers: int
    utilisation_percentage: float


class DailyReportData(APIModel):
    date: date_type
    total_trips: int
    completed_trips: int
    cancelled_trips: int
    total_passengers: int


class FleetReportData(APIModel):
    vehicle_id: str
    registration_number: str
    utilisation_percentage: float
    maintenance_events: int
    total_km: float
    status: str


class DriverReportData(APIModel):
    driver_id: str
    driver_name: str
    trips_completed: int
    on_time_rate: float
    avg_trip_duration_minutes: float
    total_passengers: int


class FilteredReportResponse(APIModel):
    report_type: Literal["route", "daily", "fleet", "driver"]
    filters_applied: dict
    generated_at: datetime
    data: list[
        Union[RouteReportData, DailyReportData, FleetReportData, DriverReportData]
    ]


class PassengerTripRecord(APIModel):
    trip_id: str
    trip_date: str
    route_name: str
    boarding_stop: Optional[str] = None
    alighting_stop: Optional[str] = None
    scheduled_departure: Optional[str] = None
    actual_departure: Optional[str] = None
    scheduled_arrival: Optional[str] = None
    actual_arrival: Optional[str] = None
    on_time: bool = False


class PassengerReportResponse(APIModel):
    passenger_id: str
    passenger_name: str
    date_from: str
    date_to: str
    generated_at: str
    message: Optional[str] = None
    data: List[PassengerTripRecord] = []


class RouteUsageCount(APIModel):
    route_name: str
    count: int


class StopUsageCount(APIModel):
    stop_name: str
    count: int


class BoardingTimelineEntry(APIModel):
    recorded_at: str
    route_name: str
    stop_name: str
    event_type: str


class PassengerUsageReport(APIModel):
    passenger_id: str
    passenger_name: str
    email: str
    date_from: str
    date_to: str
    generated_at: str
    total_boardings: int
    total_alightings: int
    most_used_routes: List[RouteUsageCount]
    most_used_stops: List[StopUsageCount]
    timeline: List[BoardingTimelineEntry]
    message: Optional[str] = None
