"""Service for generating superadmin passenger usage reports."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.boarding_record import BoardingRecord
from app.models.route import Route, Stop
from app.models.trip import Trip
from app.models.user import User
from app.schemas.analytics import (
    BoardingTimelineEntry,
    PassengerUsageReport,
    RouteUsageCount,
    StopUsageCount,
)


def _error_detail(code: str, message: str) -> dict:
    return {"data": None, "meta": None, "error": {"code": code, "message": message}}


async def get_passenger_usage_report(
    db: AsyncSession,
    passenger_id: str,
    date_from: date,
    date_to: date,
) -> PassengerUsageReport:
    user = await db.scalar(select(User).where(User.id == passenger_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_error_detail("NOT_FOUND", "Passenger not found"),
        )
    if user.role != "passenger":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_error_detail("FORBIDDEN", "User is not a passenger"),
        )

    start_dt = datetime.combine(date_from, time.min, tzinfo=timezone.utc)
    end_dt = datetime.combine(
        date_to + timedelta(days=1), time.min, tzinfo=timezone.utc
    )

    stmt = (
        select(
            BoardingRecord.recorded_at,
            Stop.name.label("stop_name"),
            Route.name.label("route_name"),
            Trip.status.label("trip_status"),
        )
        .outerjoin(Stop, BoardingRecord.stop_id == Stop.id)
        .outerjoin(Trip, BoardingRecord.trip_id == Trip.id)
        .outerjoin(Route, Trip.route_id == Route.id)
        .where(
            BoardingRecord.passenger_id == passenger_id,
            BoardingRecord.event_type == "boarded",
            BoardingRecord.recorded_at >= start_dt,
            BoardingRecord.recorded_at < end_dt,
        )
        .order_by(BoardingRecord.recorded_at.asc())
    )

    rows = (await db.execute(stmt)).all()

    if not rows:
        return PassengerUsageReport(
            passenger_id=passenger_id,
            passenger_name=user.full_name or user.email,
            email=user.email,
            date_from=date_from.isoformat(),
            date_to=date_to.isoformat(),
            generated_at=datetime.now(timezone.utc).isoformat(),
            total_boardings=0,
            most_used_routes=[],
            most_used_stops=[],
            timeline=[],
            message=(
                "No journey data recorded for this passenger in the selected period."
            ),
        )

    route_counts: dict[str, int] = {}
    stop_counts: dict[str, int] = {}
    timeline: list[BoardingTimelineEntry] = []

    for row in rows:
        route_name = row.route_name or "Unknown Route"
        stop_name = row.stop_name or "Unknown Stop"
        trip_status = row.trip_status or "unknown"

        route_counts[route_name] = route_counts.get(route_name, 0) + 1
        stop_counts[stop_name] = stop_counts.get(stop_name, 0) + 1
        timeline.append(
            BoardingTimelineEntry(
                boarded_at=row.recorded_at.isoformat(),
                route_name=route_name,
                stop_name=stop_name,
                trip_status=trip_status,
            )
        )

    most_used_routes = sorted(
        [RouteUsageCount(route_name=k, count=v) for k, v in route_counts.items()],
        key=lambda x: x.count,
        reverse=True,
    )
    most_used_stops = sorted(
        [StopUsageCount(stop_name=k, count=v) for k, v in stop_counts.items()],
        key=lambda x: x.count,
        reverse=True,
    )

    return PassengerUsageReport(
        passenger_id=passenger_id,
        passenger_name=user.full_name or user.email,
        email=user.email,
        date_from=date_from.isoformat(),
        date_to=date_to.isoformat(),
        generated_at=datetime.now(timezone.utc).isoformat(),
        total_boardings=len(rows),
        most_used_routes=most_used_routes,
        most_used_stops=most_used_stops,
        timeline=timeline,
    )
