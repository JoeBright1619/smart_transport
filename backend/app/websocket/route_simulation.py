from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from random import randint, random, uniform
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.geo_math import bearing, haversine_distance, move_along_bearing
from app.models.route import RouteStop, Stop
from app.models.vehicle import Vehicle
from app.websocket.route_trip_records import complete_trip, end_journey, start_trip

TICK_SECONDS = 5
OPEN_ROAD_SPEED = 35
DECEL_START_DIST = 250
# Fuel is drawn down over the whole journey (no per-loop top-up) and only refilled at the
# depot when the journey ends. The rate is deliberately higher than real life so a
# multi-round journey visibly depletes and can cross LOW_FUEL_THRESHOLD.
FUEL_CONSUMPTION_PCT_PER_KM = 2.5
LOW_FUEL_THRESHOLD = 15
DWELL_TICKS = 2

# Traffic congestion: a moving vehicle occasionally gets stuck crawling for a while, which
# accrues real delay. If a single jam lasts past DELAY_ALERT_MINUTES the runner raises a
# delay alert (once per journey). Tunable — raise the chance to see delays sooner.
CONGESTION_CHANCE = 0.015
CONGESTION_MIN_TICKS = 24
CONGESTION_MAX_TICKS = 48
CONGESTION_SPEED = 7
DELAY_ALERT_MINUTES = 2

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

    # A running vehicle must always have exactly one active trip (adopt an existing open
    # trip, or create one). Doing this every tick — not only when the terminal is reached
    # — means Dispatch always reflects moving vehicles and there is no gap on the return
    # leg or after a mid-journey route change.
    await start_trip(db, vehicle, state, now)

    # Bus pauses at each stop for DWELL_TICKS before moving on
    dwell = int(state.get("dwell_remaining", 0))
    if dwell > 0:
        state["dwell_remaining"] = dwell - 1
        fuel_pct = float(
            state.get("fuel_pct", vehicle.fuel if vehicle.fuel is not None else 100)
        )
        vehicle.fuel = round(fuel_pct)
        return {
            "lat": vehicle.lat,
            "lng": vehicle.lng,
            "speed": 0,
            "heading": vehicle.heading or 0,
            "fuel": round(fuel_pct),
            "fuel_drop": 0.0,
        }

    target = stops[int(state["next_stop_index"])]
    dist_m = haversine_distance(vehicle.lat, vehicle.lng, target.lat, target.lng)
    current_speed = vehicle.speed or 0

    # Traffic congestion crawls the vehicle and accrues delay; a long jam raises an alert.
    in_congestion, delay_crossed = _update_congestion(state)

    if in_congestion:
        new_speed = CONGESTION_SPEED
    elif current_speed == 0:
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
        state["dwell_remaining"] = DWELL_TICKS
        state["at_stop_name"] = stops[current_stop_index].name

        # await simulate_passengers_at_stop(
        #    db, vehicle, stops, current_stop_index, state, now
        # )
        # Legacy passenger simulation disabled (Phase 7.4 cutover).
        # The replacement runs in passenger_service and is consumed via
        # MQTT (gps/+/+/occupancy) by OccupancyMQTTSubscriber.

        if state["next_stop_index"] == 0:
            # One full loop of the route done. Track it on the vehicle (persists across
            # restarts, unlike the in-memory state) so the rounds cap is durable.
            vehicle.completed_loops = (vehicle.completed_loops or 0) + 1
            state["loop_count"] = vehicle.completed_loops
            if _journey_is_done(vehicle):
                # Ran the planned number of rounds — complete the final loop's trip and
                # park the vehicle. No new trip is started on the next tick because the
                # vehicle is now idle and drops out of the active-vehicle query.
                await end_journey(db, vehicle, state, now)
                clear_vehicle_state(vehicle.id)
                return {
                    "lat": lat,
                    "lng": lng,
                    "speed": 0,
                    "heading": heading,
                    "fuel": vehicle.fuel if vehicle.fuel is not None else 0,
                    "fuel_drop": 0.0,
                }
            await complete_trip(db, vehicle, state, now)
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
    # Fuel only ever draws down here; the tank is refilled at the depot when the journey
    # ends (see end_journey / trip completion), not every loop.
    new_fuel = max(0, fuel_pct - fuel_drop)

    state["fuel_pct"] = new_fuel
    vehicle.fuel = round(new_fuel)

    return {
        "lat": lat,
        "lng": lng,
        "speed": speed,
        "heading": heading,
        "fuel": round(new_fuel),
        "fuel_drop": fuel_drop,
        "delay_crossed": delay_crossed,
    }


def _update_congestion(state: dict[str, Any]) -> tuple[bool, bool]:
    """Advance the vehicle's congestion state one tick.

    Returns ``(in_congestion, delay_crossed)``: whether the vehicle is crawling in traffic
    this tick, and whether the current jam has just passed DELAY_ALERT_MINUTES (fires once
    per journey — the flag resets when the sim state is cleared on journey start/end).
    """
    remaining = int(state.get("congestion_ticks", 0))
    if remaining <= 0 and random() < CONGESTION_CHANCE:  # nosec B311
        remaining = randint(CONGESTION_MIN_TICKS, CONGESTION_MAX_TICKS)  # nosec B311

    if remaining <= 0:
        state["congestion_ticks"] = 0
        state["congestion_run_min"] = 0.0
        return (False, False)

    state["congestion_ticks"] = remaining - 1
    run_min = float(state.get("congestion_run_min", 0.0)) + TICK_SECONDS / 60
    state["congestion_run_min"] = run_min

    delay_crossed = False
    if run_min >= DELAY_ALERT_MINUTES and not state.get("delay_alerted"):
        state["delay_alerted"] = True
        delay_crossed = True
    return (True, delay_crossed)


def _journey_is_done(vehicle: Vehicle) -> bool:
    """True when a capped journey has finished its planned number of loops.

    A ``planned_loops`` of ``None`` means the journey is uncapped and loops indefinitely.
    """
    return (
        vehicle.planned_loops is not None
        and (vehicle.completed_loops or 0) >= vehicle.planned_loops
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
