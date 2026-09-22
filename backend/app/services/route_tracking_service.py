"""Route tracking service - detects route events from GPS positions.

This service monitors vehicle positions and detects when:
- A vehicle arrives at a stop
- A vehicle completes a route loop (returns to terminal)
- A journey is complete

It works with BOTH internal simulation AND external GPS sources.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.websocket.route_trip_records import complete_trip, end_journey, start_trip

if TYPE_CHECKING:
    from app.models.vehicle import Vehicle

logger = logging.getLogger(__name__)

STOP_ARRIVAL_THRESHOLD_METERS = 30


class RouteEventType(str, Enum):
    STOP_ARRIVAL = "stop_arrival"
    LOOP_COMPLETE = "loop_complete"
    JOURNEY_COMPLETE = "journey_complete"


@dataclass
class RouteEvent:
    """Event emitted when a vehicle reaches a significant route point."""

    event_type: RouteEventType
    vehicle_id: str
    tenant_id: str
    stop_id: str | None = None
    stop_name: str | None = None
    stop_index: int | None = None
    timestamp: datetime | None = None


# In-memory state for route tracking
_vehicle_states: dict[str, dict[str, Any]] = {}
_route_stops_cache: dict[str, list[Any]] = {}


async def track_gps_update(
    db: AsyncSession,
    vehicle: Vehicle,
    gps_data: dict[str, Any],
) -> list[RouteEvent]:
    """Track GPS update and emit route events when detected.

    Works with both internal simulation AND external GPS sources.
    """
    events: list[RouteEvent] = []

    if vehicle.route_id is None:
        return events

    state = _get_or_init_state(vehicle.id)
    stops = await _get_route_stops(db, vehicle.route_id)

    if len(stops) < 2:
        return events

    now = datetime.now(timezone.utc)
    current_stop_index = int(state.get("next_stop_index", 0))
    target_stop = stops[current_stop_index]

    from app.core.geo_math import haversine_distance

    dist_to_stop = haversine_distance(
        gps_data["lat"], gps_data["lng"], target_stop.lat, target_stop.lng
    )

    # Check if vehicle arrived at stop
    if dist_to_stop < STOP_ARRIVAL_THRESHOLD_METERS or gps_data.get("speed", 0) == 0:
        arrived_stop = stops[current_stop_index]

        # Emit stop arrival event
        events.append(
            RouteEvent(
                event_type=RouteEventType.STOP_ARRIVAL,
                vehicle_id=vehicle.id,
                tenant_id=vehicle.tenant_id,
                stop_id=arrived_stop.id,
                stop_name=arrived_stop.name,
                stop_index=current_stop_index,
                timestamp=now,
            )
        )

        # Handle stop arrival (passengers)
        await _handle_stop_arrival(db, vehicle, state, stops, current_stop_index, now)

        # Advance to next stop
        next_index = (current_stop_index + 1) % len(stops)
        state["next_stop_index"] = next_index
        state["dwell_remaining"] = 2
        state["at_stop_name"] = arrived_stop.name

        # Check loop completion
        if next_index == 0:
            loop_event = await _handle_loop_complete(db, vehicle, state, now)
            if loop_event:
                events.append(loop_event)

        # Start/continue trip
        await start_trip(db, vehicle, state, now)

        logger.debug("Tracked GPS for vehicle %s: events=%d", vehicle.id, len(events))
    return events


async def _handle_stop_arrival(
    db: AsyncSession,
    vehicle: Vehicle,
    state: dict[str, Any],
    stops: list[Any],
    stop_index: int,
    now: datetime,
) -> None:
    """Handle passenger boarding/alighting when vehicle arrives at a stop."""
    from app.websocket.passenger_simulation import simulate_passengers_at_stop

    try:
        await simulate_passengers_at_stop(
            db=db,
            vehicle=vehicle,
            stops=stops,
            current_stop_index=stop_index,
            state=state,
            now=now,
        )
        logger.debug(
            "Processed passengers at stop for vehicle %s",
            vehicle.id,
        )
    except Exception as e:
        logger.warning(
            "Passenger simulation failed for vehicle %s: %s",
            vehicle.id,
            str(e),
        )


async def _handle_loop_complete(
    db: AsyncSession,
    vehicle: Vehicle,
    state: dict[str, Any],
    now: datetime,
) -> RouteEvent | None:
    """Handle completion of a full route loop."""
    vehicle.completed_loops = (vehicle.completed_loops or 0) + 1
    state["loop_count"] = vehicle.completed_loops

    if vehicle.planned_loops and vehicle.completed_loops >= vehicle.planned_loops:
        await end_journey(db, vehicle, state, now)
        clear_vehicle_state(vehicle.id)

        return RouteEvent(
            event_type=RouteEventType.JOURNEY_COMPLETE,
            vehicle_id=vehicle.id,
            tenant_id=vehicle.tenant_id,
            timestamp=now,
        )

    await complete_trip(db, vehicle, state, now)

    return RouteEvent(
        event_type=RouteEventType.LOOP_COMPLETE,
        vehicle_id=vehicle.id,
        tenant_id=vehicle.tenant_id,
        timestamp=now,
    )


async def _get_route_stops(db: AsyncSession, route_id: str) -> list[Any]:
    """Get route stops, cached in memory."""
    global _route_stops_cache

    if route_id not in _route_stops_cache:
        from app.models.route import RouteStop, Stop

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

        @dataclass
        class SimpleStop:
            id: str
            name: str
            lat: float
            lng: float

        _route_stops_cache[route_id] = [
            SimpleStop(id=row[0], name=row[1], lat=row[2], lng=row[3]) for row in rows
        ]

    return _route_stops_cache[route_id]


def _get_or_init_state(vehicle_id: str) -> dict[str, Any]:
    """Get or initialize per-vehicle state for route tracking."""
    global _vehicle_states

    if vehicle_id not in _vehicle_states:
        _vehicle_states[vehicle_id] = {
            "current_trip_id": None,
            "trip_started_at": None,
            "next_stop_index": 0,
            "dwell_remaining": 0,
            "at_stop_name": None,
            "passengers": [],
            "passenger_pool": [],
            "loop_count": 0,
            "fuel_pct": 100,
        }

    return _vehicle_states[vehicle_id]


def get_vehicle_state(vehicle_id: str) -> dict[str, Any] | None:
    """Get the current route tracking state for a vehicle."""
    return _vehicle_states.get(vehicle_id)


def clear_vehicle_state(vehicle_id: str) -> bool:
    """Clear the route tracking state for a vehicle.

    Call this when a vehicle goes offline, journey ends, or is removed.
    """
    global _vehicle_states
    if vehicle_id in _vehicle_states:
        del _vehicle_states[vehicle_id]
        return True
    return False


def clear_all_states() -> None:
    """Clear all vehicle states. Use on service restart."""
    global _vehicle_states, _route_stops_cache
    _vehicle_states.clear()
    _route_stops_cache.clear()
