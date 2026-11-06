"""Route position helpers for the arrivals and tracking services.

Extracted from app.websocket.route_simulation when the in-process
vehicle simulation was removed (gps_service Phase 5, Task 5.3a).
These helpers compute route position from the vehicle's current
lat/lng + the route's stops, without the in-memory `_state` dict the
old simulation kept.

Design note on next_stop_index: gps_service tracks the true
next_stop_index in its SimulationEngine state but does not publish it.
This module derives an approximation from position (nearest stop + 1,
assuming single-loop cycling). Known limitation: right after a vehicle
leaves stop A and is closer to B than to A, this returns "next = C"
while gps_service's true value is B. Matches the pre-existing fallback
in arrival_service; not worse than today. Task 5.7 (evaluate after
5.3b) may wire nextStopId through MQTT to eliminate the approximation.

Callers:
- app.services.arrival_service — ETA computation for /api/v1/arrivals
- app.websocket.tracking — the vehicle_update WebSocket message
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.geo_math import haversine_distance
from app.models.route import RouteStop, Stop
from app.models.vehicle import Vehicle

# Per-process route stop cache; loaded on demand, kept until restart.
_route_stops_cache: dict[str, list["StopPoint"]] = {}


@dataclass(frozen=True)
class StopPoint:
    """Route stop data needed by the tracking/arrivals services."""

    id: str
    name: str
    lat: float
    lng: float


async def load_route_stops(db: AsyncSession, route_id: str) -> list[StopPoint]:
    """Load a route's ordered stops from the DB (no cache)."""

    rows = (
        await db.execute(
            select(Stop.id, Stop.name, Stop.lat, Stop.lng)
            .join(RouteStop, RouteStop.stop_id == Stop.id)
            .where(
                RouteStop.route_id == route_id,
                Stop.is_deleted.is_(False),
            )
            .order_by(RouteStop.stop_order)
        )
    ).all()
    return [
        StopPoint(id=id_, name=name, lat=lat, lng=lng) for id_, name, lat, lng in rows
    ]


async def get_stops_cached(db: AsyncSession, route_id: str) -> list[StopPoint]:
    """Load route stops once per route and keep them in memory until restart."""
    if route_id not in _route_stops_cache:
        _route_stops_cache[route_id] = await load_route_stops(db, route_id)
    return _route_stops_cache[route_id]


def compute_next_stop_index(vehicle: Vehicle, stops: list[StopPoint]) -> int:
    """Approximate the vehicle's next stop from its current position.

    Returns (nearest_stop_index + 1) % len(stops) — matching the
    pre-existing fallback in arrival_service._fallback_next_stop_index.

    See module docstring for the known limitation (drift when a vehicle
    has just left a stop and is closer to the next stop than the one it
    just departed).
    """
    if not stops or vehicle.lat is None or vehicle.lng is None:
        return 0

    nearest_index = min(
        range(len(stops)),
        key=lambda i: haversine_distance(
            vehicle.lat, vehicle.lng, stops[i].lat, stops[i].lng
        ),
    )
    return (nearest_index + 1) % len(stops)


def get_next_stop_name(vehicle: Vehicle, stops: list[StopPoint]) -> str:
    """Return the name of the vehicle's next stop, or "" if unknown."""
    if not stops:
        return ""
    idx = compute_next_stop_index(vehicle, stops)
    if 0 <= idx < len(stops):
        return stops[idx].name
    return ""


def compute_progress_pct(vehicle: Vehicle, stops: list[StopPoint]) -> int:
    """Progress percentage along the current route segment (0-100)."""
    if len(stops) < 2 or vehicle.lat is None or vehicle.lng is None:
        return 0

    next_stop_index = compute_next_stop_index(vehicle, stops)
    previous_stop = stops[(next_stop_index - 1) % len(stops)]
    next_stop = stops[next_stop_index]
    segment_length = haversine_distance(
        previous_stop.lat, previous_stop.lng, next_stop.lat, next_stop.lng
    )
    if segment_length <= 0:
        return 0

    remaining = haversine_distance(
        vehicle.lat, vehicle.lng, next_stop.lat, next_stop.lng
    )
    progress = (1 - remaining / segment_length) * 100
    return int(max(0, min(100, progress)))
