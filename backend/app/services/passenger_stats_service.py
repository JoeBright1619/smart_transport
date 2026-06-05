"""Passenger journey statistics derived from boarding records."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.boarding_record import BoardingRecord
from app.models.route import Route, Stop
from app.models.trip import Trip
from app.schemas.passenger import PassengerStatsRead, RouteUsage, WeeklyTrips

_MIN_TRIPS_FOR_STATS = 3


def _ensure_aware(dt: datetime) -> datetime:
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


async def get_passenger_stats(
    db: AsyncSession, passenger_id: str
) -> PassengerStatsRead:
    """Compute journey statistics for a passenger from their boarding records."""
    now = datetime.now(timezone.utc)

    rows = (
        await db.execute(
            select(
                BoardingRecord.id,
                BoardingRecord.recorded_at,
                BoardingRecord.stop_id,
                Stop.name.label("stop_name"),
                Trip.route_id,
                Route.name.label("route_name"),
                Trip.actual_start,
                Trip.scheduled_start,
            )
            .outerjoin(Stop, Stop.id == BoardingRecord.stop_id)
            .outerjoin(Trip, Trip.id == BoardingRecord.trip_id)
            .outerjoin(Route, Route.id == Trip.route_id)
            .where(
                BoardingRecord.passenger_id == passenger_id,
                BoardingRecord.event_type == "boarded",
            )
            .order_by(BoardingRecord.recorded_at.desc())
        )
    ).all()

    total_trips = len(rows)

    # Routes used (top 5)
    route_counts: dict[str, dict] = {}
    for row in rows:
        if row.route_id:
            if row.route_id not in route_counts:
                route_counts[row.route_id] = {
                    "name": row.route_name or "Unknown Route",
                    "count": 0,
                }
            route_counts[row.route_id]["count"] += 1

    routes_used = sorted(
        [
            RouteUsage(route_id=rid, route_name=v["name"], trip_count=v["count"])
            for rid, v in route_counts.items()
        ],
        key=lambda r: r.trip_count,
        reverse=True,
    )[:5]

    # Favourite boarding stop
    stop_counts: dict[str, int] = {}
    for row in rows:
        if row.stop_name:
            stop_counts[row.stop_name] = stop_counts.get(row.stop_name, 0) + 1
    favourite_stop = (
        max(stop_counts, key=lambda k: stop_counts[k]) if stop_counts else None
    )

    # On-time rate and average wait
    timed = [
        (row.actual_start, row.scheduled_start)
        for row in rows
        if row.actual_start is not None and row.scheduled_start is not None
    ]
    if timed:
        on_time = sum(
            1
            for a, s in timed
            if (_ensure_aware(a) - _ensure_aware(s)).total_seconds() <= 300
        )
        on_time_rate = round((on_time / len(timed)) * 100, 1)
        avg_wait_minutes = round(
            sum(
                max(0.0, (_ensure_aware(a) - _ensure_aware(s)).total_seconds() / 60)
                for a, s in timed
            )
            / len(timed),
            1,
        )
    else:
        on_time_rate = 0.0
        avg_wait_minutes = 0.0

    # Weekly trip counts (last 4 calendar weeks, Mon–Sun)
    today = now.date()
    monday_this_week = today - timedelta(days=today.weekday())
    week_starts = [monday_this_week - timedelta(weeks=i) for i in range(4)]
    week_counts = [0, 0, 0, 0]

    for row in rows:
        dt = _ensure_aware(row.recorded_at)
        record_date = dt.date()
        for i, ws in enumerate(week_starts):
            if ws <= record_date < ws + timedelta(days=7):
                week_counts[i] += 1
                break

    # Build oldest-to-newest for the chart
    weekly_trips = [
        WeeklyTrips(
            week_label=week_starts[i].strftime("%b %d"),
            trips=week_counts[i],
        )
        for i in range(3, -1, -1)
    ]

    return PassengerStatsRead(
        total_trips=total_trips,
        routes_used=routes_used,
        favourite_stop=favourite_stop,
        on_time_rate=on_time_rate,
        avg_wait_minutes=avg_wait_minutes,
        this_week_trips=week_counts[0],
        last_week_trips=week_counts[1],
        weekly_trips=weekly_trips,
        has_enough_data=total_trips >= _MIN_TRIPS_FOR_STATS,
    )
