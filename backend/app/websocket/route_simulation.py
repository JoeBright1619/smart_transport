from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.geo_math import haversine_distance
from app.models.route import RouteStop, Stop
from app.models.vehicle import Vehicle

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
