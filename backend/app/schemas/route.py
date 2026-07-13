from datetime import datetime
from typing import Any

from pydantic import Field, computed_field

from app.schemas.base import APIModel


class StopCreate(APIModel):
    name: str = Field(
        min_length=1, max_length=100, json_schema_extra={"example": "Nyabugogo"}
    )
    lat: float = Field(ge=-90, le=90, json_schema_extra={"example": -1.9396})
    lng: float = Field(ge=-180, le=180, json_schema_extra={"example": 30.0585})


class StopUpdate(APIModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        json_schema_extra={"example": "Nyabugogo"},
    )
    lat: float | None = Field(
        default=None, ge=-90, le=90, json_schema_extra={"example": -1.9396}
    )
    lng: float | None = Field(
        default=None, ge=-180, le=180, json_schema_extra={"example": 30.0585}
    )


class GlobalStopRead(APIModel):
    id: str = Field(json_schema_extra={"example": "stop-uuid"})
    name: str = Field(json_schema_extra={"example": "Nyabugogo"})
    lat: float = Field(json_schema_extra={"example": -1.9396})
    lng: float = Field(json_schema_extra={"example": 30.0585})


class RouteStopCreate(APIModel):
    stop_id: str = Field(json_schema_extra={"example": "stop-uuid"})
    order: int = Field(ge=1, json_schema_extra={"example": 1})


class StopRead(GlobalStopRead):
    order: int = Field(json_schema_extra={"example": 1})


class RouteCreate(APIModel):
    name: str = Field(
        min_length=1,
        max_length=100,
        json_schema_extra={"example": "Nyabugogo - Kimironko"},
    )
    number: str = Field(
        min_length=1, max_length=20, json_schema_extra={"example": "101"}
    )
    distance: float = Field(ge=0, json_schema_extra={"example": 12.5})
    duration: int = Field(ge=0, json_schema_extra={"example": 35})
    color: str = Field(
        min_length=4, max_length=9, json_schema_extra={"example": "#3B82F6"}
    )
    stops: list[RouteStopCreate] = Field(min_length=1)


class RouteUpdate(APIModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        json_schema_extra={"example": "Nyabugogo - Kimironko Express"},
    )
    number: str | None = Field(
        default=None,
        min_length=1,
        max_length=20,
        json_schema_extra={"example": "101X"},
    )
    distance: float | None = Field(
        default=None, ge=0, json_schema_extra={"example": 12.5}
    )
    duration: int | None = Field(default=None, ge=0, json_schema_extra={"example": 35})
    is_active: bool | None = Field(default=None, json_schema_extra={"example": False})
    color: str | None = Field(
        default=None,
        min_length=4,
        max_length=9,
        json_schema_extra={"example": "#EF4444"},
    )
    stops: list[RouteStopCreate] | None = Field(default=None)


class RouteRead(APIModel):
    id: str = Field(json_schema_extra={"example": "route-uuid"})
    name: str = Field(json_schema_extra={"example": "Nyabugogo - Kimironko"})
    number: str = Field(json_schema_extra={"example": "101"})
    distance: float = Field(json_schema_extra={"example": 12.5})
    duration: int = Field(json_schema_extra={"example": 35})
    color: str = Field(json_schema_extra={"example": "#3B82F6"})
    is_active: bool = Field(json_schema_extra={"example": True})
    created_at: datetime = Field(json_schema_extra={"example": "2026-04-01T08:00:00Z"})

    route_stops: list[Any] = Field(default_factory=list, exclude=True)

    @computed_field
    def stops(self) -> list[StopRead]:
        result = []
        for rs in sorted(self.route_stops, key=lambda x: getattr(x, "stop_order", 0)):
            stop = getattr(rs, "stop", None)
            if stop:
                result.append(
                    StopRead(
                        id=stop.id,
                        name=stop.name,
                        lat=stop.lat,
                        lng=stop.lng,
                        order=getattr(rs, "stop_order", 0),
                    )
                )
        return result
