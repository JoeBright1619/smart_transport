from datetime import date as date_type

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
