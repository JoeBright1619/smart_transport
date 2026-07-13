"""Passenger boarding and alighting simulation for route stops."""

from __future__ import annotations

from datetime import datetime
from random import randint, sample
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.geo_math import haversine_distance
from app.crud.analytics import upsert_daily_analytics
from app.models.user import User
from app.models.vehicle import Vehicle
from app.services import boarding_service
from app.websocket.manager import manager


# Global set of passenger IDs currently on board any vehicle.
# Prevents the same real passenger from being assigned to two buses simultaneously.
_globally_on_board: set[str] = set()

# A terminal can load beyond seated capacity up to this multiple (standing/overcrowding),
# which is what lets occupancy reach and exceed capacity to trip the capacity alert.
CRUSH_CAPACITY_FACTOR = 1.15


async def load_passenger_pool(db: AsyncSession, state: dict[str, Any]) -> list[str]:
    """Load real passenger IDs once into vehicle state; no-op on repeat calls."""
    if "passenger_pool" not in state:
        rows = await db.scalars(
            select(User.id).where(User.role == "passenger", User.is_deleted.is_(False))
        )
        state["passenger_pool"] = list(rows.all())
    return state["passenger_pool"]


def _assign_passenger_ids(
    new_entries: list[dict[str, Any]],
    pool: list[str],
    excluded_ids: set[str],
) -> list[str]:
    """Randomly assign real IDs to a subset of new boarders; mutates entries in-place."""
    available = [pid for pid in pool if pid not in excluded_ids]
    n = min(len(new_entries), len(available))
    if not n:
        return []
    selected = sample(available, n)  # nosec B311
    for entry, pid in zip(new_entries, selected):
        entry["passenger_id"] = pid
    return selected


async def simulate_passengers_at_stop(
    db: AsyncSession,
    vehicle: Vehicle,
    stops: list[Any],
    current_stop_index: int,
    state: dict[str, Any],
    now: datetime,
) -> None:
    """Simulate passengers boarding and alighting at a stop and calculate revenue."""
    pool = await load_passenger_pool(db, state)

    passengers = state.setdefault("passengers", [])
    is_terminal = current_stop_index == 0
    is_last_stop = current_stop_index == len(stops) - 1
    capacity = vehicle.seating_capacity

    # 1. Alight passengers (keep through-passengers at the last stop)
    remaining_passengers: list[dict[str, Any]] = []
    revenue = 0.0
    alighted_count = 0
    tracked_alighted_ids: list[str] = []

    if is_last_stop and len(stops) > 2:
        n_through = min(randint(3, 6), len(passengers))  # nosec B311
        for i, p in enumerate(passengers):
            if i < n_through:
                pid = p.get("passenger_id")
                if pid:
                    # Close the board→alight pair at the route boundary so the
                    # passenger's trip history stays consistent, then carry them
                    # forward as anonymous for the next leg.
                    tracked_alighted_ids.append(pid)
                remaining_passengers.append(
                    {
                        "origin_index": 0,
                        "dest_index": randint(1, len(stops) - 1),  # nosec B311
                        "distance_km": 1.0,
                        "passenger_id": None,
                    }
                )
            elif p["dest_index"] == current_stop_index:
                revenue += p["distance_km"] * 60.0
                alighted_count += 1
                if p.get("passenger_id"):
                    tracked_alighted_ids.append(p["passenger_id"])
            else:
                remaining_passengers.append(p)
    else:
        for p in passengers:
            if p["dest_index"] == current_stop_index:
                revenue += p["distance_km"] * 60.0
                alighted_count += 1
                if p.get("passenger_id"):
                    tracked_alighted_ids.append(p["passenger_id"])
            else:
                remaining_passengers.append(p)

    # 2. Board new passengers
    boarded_count = 0
    available_seats = capacity - len(remaining_passengers)
    new_entries: list[dict[str, Any]] = []

    if is_terminal and len(stops) > 1:
        # A busy terminal usually loads most seats, but can overcrowd (standing
        # passengers) up to a crush level — which is what trips the capacity alert. Board
        # against the crush headroom, not just seated capacity.
        crush_capacity = int(capacity * CRUSH_CAPACITY_FACTOR)
        headroom = crush_capacity - len(remaining_passengers)
        target = randint(int(capacity * 0.75), int(capacity * 1.10))  # nosec B311
        boarded_count = max(0, min(target, headroom))
        for _ in range(boarded_count):
            dest_index = randint(1, len(stops) - 1)  # nosec B311
            dist_m = sum(
                haversine_distance(
                    stops[i].lat, stops[i].lng, stops[i + 1].lat, stops[i + 1].lng
                )
                for i in range(0, dest_index)
            )
            new_entries.append(
                {
                    "origin_index": current_stop_index,
                    "dest_index": dest_index,
                    "distance_km": dist_m / 1000.0,
                    "passenger_id": None,
                }
            )
    elif not is_last_stop and available_seats > 0:
        board_cap = max(1, capacity // 6)
        lower = min(max(1, board_cap // 2), available_seats)
        upper = min(board_cap, available_seats)
        boarded_count = randint(lower, upper)  # nosec B311
        for _ in range(boarded_count):
            dest_index = randint(current_stop_index + 1, len(stops) - 1)  # nosec B311
            dist_m = sum(
                haversine_distance(
                    stops[i].lat, stops[i].lng, stops[i + 1].lat, stops[i + 1].lng
                )
                for i in range(current_stop_index, dest_index)
            )
            new_entries.append(
                {
                    "origin_index": current_stop_index,
                    "dest_index": dest_index,
                    "distance_km": dist_m / 1000.0,
                    "passenger_id": None,
                }
            )

    # Assign real passenger IDs to a random subset of the new boarders.
    # Exclude: passengers on this vehicle, those who just alighted here (no same-stop
    # reboard), and any ID already riding another vehicle (_globally_on_board).
    on_board_ids = {
        p["passenger_id"] for p in remaining_passengers if p.get("passenger_id")
    }
    excluded_ids = on_board_ids | set(tracked_alighted_ids) | _globally_on_board
    tracked_board_ids = _assign_passenger_ids(new_entries, pool, excluded_ids)
    _globally_on_board.update(tracked_board_ids)
    _globally_on_board.difference_update(tracked_alighted_ids)

    remaining_passengers.extend(new_entries)
    state["passengers"] = remaining_passengers
    state["current_occupancy"] = len(remaining_passengers)
    occupancy_after = len(remaining_passengers)

    # 3. Persist occupancy to DB so value survives page reloads
    vehicle.current_occupancy = occupancy_after
    await db.flush()

    # 4. Broadcast immediate occupancy update
    await manager.publish_to_tenant(
        vehicle.tenant_id,
        {
            "type": "vehicle_occupancy_updated",
            "vehicleId": vehicle.id,
            "currentOccupancy": occupancy_after,
            "seatingCapacity": vehicle.seating_capacity,
            "remainingSeats": max(0, vehicle.seating_capacity - occupancy_after),
        },
    )

    # 5. Persist boarding records — individual for tracked passengers, aggregate for the rest
    stop_id = stops[current_stop_index].id
    trip_id: str | None = state.get("current_trip_id")
    route_id: str | None = vehicle.route_id

    for pid in tracked_board_ids:
        await boarding_service.record_single_boarding(
            db,
            trip_id=trip_id,
            stop_id=stop_id,
            passenger_id=pid,
            event_type="boarded",
            tenant_id=vehicle.tenant_id,
            occupancy_after=occupancy_after,
            now=now,
            route_id=route_id,
        )

    for pid in tracked_alighted_ids:
        await boarding_service.record_single_boarding(
            db,
            trip_id=trip_id,
            stop_id=stop_id,
            passenger_id=pid,
            event_type="alighted",
            tenant_id=vehicle.tenant_id,
            occupancy_after=occupancy_after,
            now=now,
            route_id=route_id,
        )

    anon_boarded = boarded_count - len(tracked_board_ids)
    anon_alighted = alighted_count - len(tracked_alighted_ids)
    if anon_boarded > 0 or anon_alighted > 0:
        await boarding_service.record_stop_events(
            db,
            vehicle,
            stop_id,
            anon_boarded,
            anon_alighted,
            occupancy_after,
            now,
            stop_name=stops[current_stop_index].name,
            route_id=route_id,
            trip_id=trip_id,
        )

    # 6. Add to live daily revenue
    if revenue > 0:
        await upsert_daily_analytics(
            db=db,
            tenant_id=vehicle.tenant_id,
            record_date=now.date(),
            revenue=revenue,
        )
