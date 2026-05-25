from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.geo_math import bearing, haversine_distance, move_along_bearing
from app.models.route import RouteStop, Stop
from app.models.vehicle import Vehicle

TICK_SECONDS = 5

_state: dict[str, dict[str, Any]] = {}


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


async def advance_vehicle(
    db: AsyncSession, vehicle: Vehicle, now: datetime
) -> dict[str, float | int] | None:
    """Advance a vehicle one simulation tick toward the next route stop."""
    if vehicle.route_id is None or vehicle.lat is None or vehicle.lng is None:
        return None

    stops = await load_route_stops(db, vehicle.route_id)
    if len(stops) < 2:
        return None

    state = get_or_init_state(vehicle.id, len(stops))
    target = stops[int(state["next_stop_index"])]
    dist_m = haversine_distance(vehicle.lat, vehicle.lng, target.lat, target.lng)
    advance_m = (vehicle.speed or 20) * 1000 / 3600 * TICK_SECONDS

    if dist_m <= advance_m or dist_m < 30:
        lat = target.lat
        lng = target.lng
        speed = 0
        heading = vehicle.heading or 0
        state["next_stop_index"] = (int(state["next_stop_index"]) + 1) % len(stops)

        if state["next_stop_index"] == 0:
            state["loop_count"] = int(state.get("loop_count", 0)) + 1
            state["trip_started_at"] = now
    else:
        brg = bearing(vehicle.lat, vehicle.lng, target.lat, target.lng)
        lat, lng = move_along_bearing(vehicle.lat, vehicle.lng, brg, advance_m)
        speed = vehicle.speed or 20
        heading = int(brg)

    return {
        "lat": lat,
        "lng": lng,
        "speed": speed,
        "heading": heading,
    }


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
