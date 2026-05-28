from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from random import uniform, randint
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.geo_math import bearing, haversine_distance, move_along_bearing
from app.crud.analytics import upsert_daily_analytics
from app.models.route import RouteStop, Stop
from app.models.vehicle import Vehicle
from app.websocket.route_trip_records import create_completed_trip

TICK_SECONDS = 5
OPEN_ROAD_SPEED = 35
DECEL_START_DIST = 250
FUEL_CONSUMPTION_PCT_PER_KM = 1.0
LOW_FUEL_THRESHOLD = 15

_state: dict[str, dict[str, Any]] = {}
_route_stops_cache: dict[str, list["StopPoint"]] = {}


@dataclass(frozen=True)
class StopPoint:
    """Route stop data needed by the route-following simulation."""

    id: str
    name: str
    lat: float
    lng: float


async def load_route_stops(db: AsyncSession, route_id: str) -> list[StopPoint]:
    """Load active stops for a route ordered by their route sequence."""
    rows = (
        await db.execute(
            select(Stop.id, Stop.name, Stop.lat, Stop.lng)
            .join(RouteStop, RouteStop.stop_id == Stop.id)
            .where(
                RouteStop.route_id == route_id,
                Stop.is_deleted.is_(False),
            )
            .order_by(RouteStop.stop_order.asc())
        )
    ).all()

    return [
        StopPoint(id=stop_id, name=name, lat=lat, lng=lng)
        for stop_id, name, lat, lng in rows
    ]


async def get_stops_cached(db: AsyncSession, route_id: str) -> list[StopPoint]:
    """Load route stops once per route and keep them in memory until restart."""
    if route_id not in _route_stops_cache:
        _route_stops_cache[route_id] = await load_route_stops(db, route_id)
    return _route_stops_cache[route_id]


async def advance_vehicle(
    db: AsyncSession, vehicle: Vehicle, now: datetime
) -> dict[str, float | int] | None:
    """Advance a vehicle one simulation tick toward the next route stop."""
    if vehicle.route_id is None or vehicle.lat is None or vehicle.lng is None:
        return None

    stops = await get_stops_cached(db, vehicle.route_id)
    if len(stops) < 2:
        return None

    state = get_or_init_state(vehicle.id, len(stops))
    target = stops[int(state["next_stop_index"])]
    dist_m = haversine_distance(vehicle.lat, vehicle.lng, target.lat, target.lng)
    current_speed = vehicle.speed or 0

    if current_speed == 0:
        new_speed = min(OPEN_ROAD_SPEED, current_speed + 8)
    elif dist_m < DECEL_START_DIST:
        ratio = dist_m / DECEL_START_DIST
        new_speed = max(5, int(OPEN_ROAD_SPEED * ratio))
    else:
        variation = round(uniform(-3, 3))  # nosec B311
        new_speed = max(15, min(50, current_speed + variation))

    vehicle.speed = new_speed
    advance_m = new_speed * 1000 / 3600 * TICK_SECONDS

    if dist_m <= advance_m or dist_m < 30:
        lat = target.lat
        lng = target.lng
        speed = 0
        heading = vehicle.heading or 0

        current_stop_index = int(state["next_stop_index"])
        state["next_stop_index"] = (current_stop_index + 1) % len(stops)

        await _simulate_passengers_at_stop(
            db, vehicle, stops, current_stop_index, state, now
        )

        if state["next_stop_index"] == 0:
            state["loop_count"] = int(state.get("loop_count", 0)) + 1
            await _create_completed_trip(db, vehicle, state, now)
            state["trip_started_at"] = now
    else:
        brg = bearing(vehicle.lat, vehicle.lng, target.lat, target.lng)
        lat, lng = move_along_bearing(vehicle.lat, vehicle.lng, brg, advance_m)
        speed = new_speed
        heading = int(brg)

    km_this_tick = new_speed * TICK_SECONDS / 3600
    fuel_drop = km_this_tick * FUEL_CONSUMPTION_PCT_PER_KM
    fuel_pct = float(
        state.get("fuel_pct", vehicle.fuel if vehicle.fuel is not None else 100)
    )
    new_fuel = max(0, fuel_pct - fuel_drop)

    if state["next_stop_index"] == 0 and state["loop_count"] > 0:
        new_fuel = 100.0

    state["fuel_pct"] = new_fuel
    vehicle.fuel = round(new_fuel)

    return {
        "lat": lat,
        "lng": lng,
        "speed": speed,
        "heading": heading,
        "fuel": round(new_fuel),
    }


async def _create_completed_trip(
    db: AsyncSession, vehicle: Vehicle, state: dict[str, Any], now: datetime
) -> None:
    """Create a completed trip for a vehicle that has finished its route loop."""
    await create_completed_trip(db, vehicle, state, now)


async def _simulate_passengers_at_stop(
    db: AsyncSession,
    vehicle: Vehicle,
    stops: list[StopPoint],
    current_stop_index: int,
    state: dict[str, Any],
    now: datetime,
) -> None:
    """Simulate passengers boarding and alighting at a stop and calculate revenue."""
    passengers = state.setdefault("passengers", [])

    # 1. Alight passengers
    remaining_passengers = []
    revenue = 0.0
    for p in passengers:
        if p["dest_index"] == current_stop_index:
            revenue += p["distance_km"] * 60.0
        else:
            remaining_passengers.append(p)

    # 2. Board new passengers
    if current_stop_index < len(stops) - 1:
        capacity = vehicle.capacity if vehicle.capacity else 30
        available_seats = capacity - len(remaining_passengers)
        boarding_count = randint(0, available_seats) if available_seats > 0 else 0  # nosec B311

        for _ in range(boarding_count):
            dest_index = randint(current_stop_index + 1, len(stops) - 1)  # nosec B311

            # calculate distance from current_stop_index to dest_index
            dist_m = 0.0
            for i in range(current_stop_index, dest_index):
                s1 = stops[i]
                s2 = stops[i + 1]
                dist_m += haversine_distance(s1.lat, s1.lng, s2.lat, s2.lng)

            remaining_passengers.append(
                {
                    "origin_index": current_stop_index,
                    "dest_index": dest_index,
                    "distance_km": dist_m / 1000.0,
                }
            )

    state["passengers"] = remaining_passengers

    # 3. Add to live daily revenue
    if revenue > 0:
        await upsert_daily_analytics(
            db=db,
            tenant_id=vehicle.tenant_id,
            record_date=now.date(),
            revenue=revenue,
        )


def get_or_init_state(vehicle_id: str, stop_count: int) -> dict[str, Any]:
    """Get route-following state for a vehicle, creating it if necessary."""
    state = _state.setdefault(
        vehicle_id,
        {
            "next_stop_index": 1,
            "trip_started_at": datetime.now(timezone.utc),
            "loop_count": 0,
        },
    )

    max_index = max(0, stop_count - 1)
    state["next_stop_index"] = max(
        0,
        min(max_index, int(state.get("next_stop_index", 0))),
    )
    return state


def clear_vehicle_state(vehicle_id: str) -> None:
    """Remove route-following state for a vehicle."""
    _state.pop(vehicle_id, None)


def get_next_stop_name(vehicle_id: str, stops: list[StopPoint]) -> str:
    """Return the next stop name for a vehicle with initialized route state."""
    state = _state.get(vehicle_id)
    if state is None or not stops:
        return ""

    next_stop_index = int(state.get("next_stop_index", 0))
    if next_stop_index < 0 or next_stop_index >= len(stops):
        return ""

    return stops[next_stop_index].name


def compute_progress_pct(
    vehicle: Vehicle, stops: list[StopPoint], state: dict[str, Any]
) -> int:
    """Calculate the current route segment progress percentage for a vehicle."""
    if len(stops) < 2 or vehicle.lat is None or vehicle.lng is None:
        return 0

    next_stop_index = int(state.get("next_stop_index", 0))
    if next_stop_index < 0 or next_stop_index >= len(stops):
        return 0

    previous_stop = stops[(next_stop_index - 1) % len(stops)]
    next_stop = stops[next_stop_index]
    segment_length = haversine_distance(
        previous_stop.lat,
        previous_stop.lng,
        next_stop.lat,
        next_stop.lng,
    )
    if segment_length <= 0:
        return 0

    remaining = haversine_distance(
        vehicle.lat,
        vehicle.lng,
        next_stop.lat,
        next_stop.lng,
    )
    progress = (1 - remaining / segment_length) * 100
    return int(max(0, min(100, progress)))
