from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import error_codes
from app.core.errors import _raise_error
from app.core.geo_math import haversine_distance
from app.models.route import Route, RouteStop, Stop
from app.models.vehicle import Vehicle
from app.models.tenant import Tenant
from app.schemas.arrival import ArrivalRead, PublicArrivalRead

if TYPE_CHECKING:
    from app.websocket.route_simulation import StopPoint


def _fallback_next_stop_index(vehicle: Vehicle, stops: list[StopPoint]) -> int:
    nearest_index = min(
        range(len(stops)),
        key=lambda index: haversine_distance(
            vehicle.lat or 0,
            vehicle.lng or 0,
            stops[index].lat,
            stops[index].lng,
        ),
    )
    return (nearest_index + 1) % len(stops)


def _next_stop_index(vehicle: Vehicle, stops: list[StopPoint]) -> int:
    from app.websocket.route_simulation import _state  # lazy: avoid circular import

    state = _state.get(vehicle.id, {})
    next_stop_index = int(state.get("next_stop_index", -1))
    if 0 <= next_stop_index < len(stops):
        return next_stop_index
    return _fallback_next_stop_index(vehicle, stops)


def _route_distance_to_stop_km(
    vehicle: Vehicle,
    stops: list[StopPoint],
    target_stop_id: str,
) -> float | None:
    target_indices = [
        index for index, stop in enumerate(stops) if stop.id == target_stop_id
    ]
    if not target_indices or vehicle.lat is None or vehicle.lng is None:
        return None

    next_stop_index = _next_stop_index(vehicle, stops)
    distance_m = haversine_distance(
        vehicle.lat,
        vehicle.lng,
        stops[next_stop_index].lat,
        stops[next_stop_index].lng,
    )
    current_index = next_stop_index

    while current_index not in target_indices:
        following_index = (current_index + 1) % len(stops)
        distance_m += haversine_distance(
            stops[current_index].lat,
            stops[current_index].lng,
            stops[following_index].lat,
            stops[following_index].lng,
        )
        current_index = following_index

    return distance_m / 1000


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
        _raise_error(
            status.HTTP_404_NOT_FOUND, error_codes.STOP_NOT_FOUND, "Stop not found"
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

    from app.websocket.route_simulation import (
        _state,
        get_stops_cached,
    )  # lazy: avoid circular import

    now = datetime.now(timezone.utc)
    arrivals: list[ArrivalRead] = []
    for vehicle, route in rows:
        if vehicle.route_id is None:
            continue

        stops = await get_stops_cached(db, vehicle.route_id)
        distance_km = _route_distance_to_stop_km(vehicle, stops, stop.id)
        if distance_km is None:
            continue

        speed = vehicle.speed or 0

        if speed == 0:
            eta_minutes = None
            estimated_arrival_time = None
            arrival_status = "stopped"
        else:
            eta_minutes = round((distance_km / speed) * 60)
            estimated_arrival_time = now + timedelta(minutes=eta_minutes)
            arrival_status = "active"

        v_state = _state.get(vehicle.id, {})
        current_occupancy = int(
            v_state.get("current_occupancy", len(v_state.get("passengers", [])))
        )
        seating_capacity = vehicle.seating_capacity
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
                current_occupancy=current_occupancy,
                seating_capacity=seating_capacity,
                remaining_seats=max(0, seating_capacity - current_occupancy),
            )
        )

    return sorted(
        arrivals,
        key=lambda item: item.eta_minutes if item.eta_minutes is not None else 10**9,
    )


async def get_cross_tenant_arrivals(
    db: AsyncSession,
    stop_id: str,
) -> list[PublicArrivalRead]:
    stop = await db.scalar(
        select(Stop).where(Stop.id == stop_id, Stop.is_deleted.is_(False))
    )
    if stop is None:
        _raise_error(
            status.HTTP_404_NOT_FOUND, error_codes.STOP_NOT_FOUND, "Stop not found"
        )

    rows = (
        await db.execute(
            select(Vehicle, Route, Tenant)
            .join(Route, Vehicle.route_id == Route.id)
            .join(Tenant, Vehicle.tenant_id == Tenant.id)
            .join(RouteStop, RouteStop.route_id == Route.id)
            .where(
                RouteStop.stop_id == stop.id,
                Vehicle.status == "active",
                Vehicle.is_deleted.is_(False),
                Vehicle.lat.is_not(None),
                Vehicle.lng.is_not(None),
                Route.is_active.is_(True),
                Route.is_deleted.is_(False),
            )
        )
    ).all()

    from app.websocket.route_simulation import (
        _state,
        get_stops_cached,
    )  # lazy: avoid circular import

    now = datetime.now(timezone.utc)
    arrivals: list[PublicArrivalRead] = []
    for vehicle, route, tenant in rows:
        if vehicle.route_id is None:
            continue

        stops = await get_stops_cached(db, vehicle.route_id)
        distance_km = _route_distance_to_stop_km(vehicle, stops, stop.id)
        if distance_km is None:
            continue

        speed = vehicle.speed or 0
        if speed == 0:
            eta_minutes = None
            estimated_arrival_time = None
            arrival_status = "stopped"
        else:
            eta_minutes = round((distance_km / speed) * 60)
            estimated_arrival_time = now + timedelta(minutes=eta_minutes)
            arrival_status = "active"

        v_state = _state.get(vehicle.id, {})
        current_occupancy = int(
            v_state.get("current_occupancy", len(v_state.get("passengers", [])))
        )
        seating_capacity = vehicle.seating_capacity
        arrivals.append(
            PublicArrivalRead(
                vehicle_id=vehicle.id,
                registration_number=vehicle.registration_number,
                route_id=route.id,
                route_name=route.name,
                route_number=route.number,
                tenant_name=tenant.name,
                distance_to_stop_km=round(distance_km, 2),
                current_speed_kmh=speed,
                eta_minutes=eta_minutes,
                estimated_arrival_time=estimated_arrival_time,
                status=arrival_status,
                current_occupancy=current_occupancy,
                seating_capacity=seating_capacity,
                remaining_seats=max(0, seating_capacity - current_occupancy),
            )
        )

    return sorted(
        arrivals,
        key=lambda item: item.eta_minutes if item.eta_minutes is not None else 10**9,
    )
