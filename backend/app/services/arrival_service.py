from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.geo import haversine
from app.models.route import Route, RouteStop, Stop
from app.models.vehicle import Vehicle
from app.schemas.arrival import ArrivalRead


def _error_detail(code: str, message: str) -> dict:
    return {
        "data": None,
        "meta": None,
        "error": {
            "code": code,
            "message": message,
        },
    }


async def get_arrivals_for_stop(
    db: AsyncSession,
    tenant_id: str,
    stop_id: str,
) -> list[ArrivalRead]:
    stop = await db.scalar(
        select(Stop).where(
            Stop.id == stop_id,
            Stop.tenant_id == tenant_id,
            Stop.is_deleted.is_(False),
        )
    )
    if stop is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_error_detail("NOT_FOUND", "Stop not found"),
        )

    rows = (
        await db.execute(
            select(Vehicle, Route)
            .join(Route, Vehicle.route_id == Route.id)
            .join(RouteStop, RouteStop.route_id == Route.id)
            .where(
                RouteStop.stop_id == stop.id,
                Vehicle.tenant_id == tenant_id,
                Vehicle.status == "active",
                Vehicle.is_deleted.is_(False),
                Vehicle.lat.is_not(None),
                Vehicle.lng.is_not(None),
                Route.tenant_id == tenant_id,
                Route.is_active.is_(True),
                Route.is_deleted.is_(False),
            )
        )
    ).all()

    now = datetime.now(timezone.utc)
    arrivals: list[ArrivalRead] = []
    for vehicle, route in rows:
        distance_km = haversine(vehicle.lat, vehicle.lng, stop.lat, stop.lng)
        speed = vehicle.speed or 0

        if speed == 0:
            eta_minutes = None
            estimated_arrival_time = None
            arrival_status = "stopped"
        else:
            eta_minutes = round((distance_km / speed) * 60)
            estimated_arrival_time = now + timedelta(minutes=eta_minutes)
            arrival_status = "active"

        arrivals.append(
            ArrivalRead(
                vehicle_id=vehicle.id,
                registration_number=vehicle.registration_number,
                route_id=route.id,
                route_name=route.name,
                distance_to_stop_km=round(distance_km, 2),
                current_speed_kmh=speed,
                eta_minutes=eta_minutes,
                estimated_arrival_time=estimated_arrival_time,
                status=arrival_status,
            )
        )

    return sorted(
        arrivals,
        key=lambda item: item.eta_minutes if item.eta_minutes is not None else 10**9,
    )
