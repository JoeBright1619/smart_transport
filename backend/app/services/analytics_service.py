import json
import logging
from datetime import date, datetime, timedelta
from typing import Any

import redis.asyncio as redis
from sqlalchemy import select, func, case, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.analytics import AnalyticsRecord
from app.models.driver import Driver
from app.models.maintenance import MaintenanceRecord
from app.models.route import Route
from app.models.trip import Trip
from app.models.vehicle import Vehicle
from app.models.user import User
from app.schemas.analytics import (
    DailyReportData,
    DriverReportData,
    FleetReportData,
    PassengerReportResponse,
    RouteReportData,
)

logger = logging.getLogger(__name__)

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


async def get_analytics(
    db: AsyncSession, tenant_id: str, from_date: date, to_date: date
) -> dict[str, Any]:
    cache_key = f"analytics:{tenant_id}:{from_date.isoformat()}:{to_date.isoformat()}"
    try:
        cached = await redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception as e:
        # Fallback if Redis is unavailable
        logger.warning(f"Failed to read from Redis cache: {e}")

    # 1. Trips aggregation
    trip_query = (
        select(
            cast(Trip.created_at, Date).label("d"),
            func.count(Trip.id).label("total_trips"),
            func.sum(case((Trip.delay <= 0, 1), else_=0)).label("on_time_trips"),
            func.sum(Trip.delay).label("total_delay"),
            func.sum(Trip.passengers).label("total_passengers"),
        )
        .where(
            Trip.tenant_id == tenant_id,
            cast(Trip.created_at, Date) >= from_date,
            cast(Trip.created_at, Date) <= to_date,
        )
        .group_by(cast(Trip.created_at, Date))
    )

    # Needs Date to be imported

    trip_res = await db.execute(trip_query)
    trip_rows = trip_res.all()

    # 2. Analytics table aggregation (for revenue, fuel)
    analytics_query = select(AnalyticsRecord).where(
        AnalyticsRecord.tenant_id == tenant_id,
        AnalyticsRecord.date >= from_date,
        AnalyticsRecord.date <= to_date,
    )
    analytics_res = await db.execute(analytics_query)
    analytics_rows = analytics_res.scalars().all()

    daily_map = {}

    # Fill daily map from trip rows
    for row in trip_rows:
        d = row.d
        if isinstance(d, datetime):
            d = d.date()
        elif isinstance(d, str):
            d = date.fromisoformat(d)

        daily_map[d] = {
            "date": d,
            "total_trips": row.total_trips or 0,
            "on_time_trips": row.on_time_trips or 0,
            "total_delay": row.total_delay or 0,
            "total_passengers": row.total_passengers or 0,
            "fuel": 0.0,
            "revenue": 0.0,
        }

    # Merge analytics rows
    for r in analytics_rows:
        d = r.date
        if d not in daily_map:
            daily_map[d] = {
                "date": d,
                "total_trips": 0,
                "on_time_trips": 0,
                "total_delay": 0,
                "total_passengers": 0,
                "fuel": 0.0,
                "revenue": 0.0,
            }
        daily_map[d]["fuel"] = r.total_fuel_consumption
        daily_map[d]["revenue"] = r.total_revenue

    # Generate continuous dates
    daily = []
    current_date = from_date
    summary_trips = 0
    summary_on_time = 0
    summary_delay = 0.0
    summary_passengers = 0
    summary_fuel = 0.0
    summary_revenue = 0.0

    while current_date <= to_date:
        d_str = current_date.isoformat()
        if current_date in daily_map:
            dm = daily_map[current_date]
            daily.append(
                {
                    "date": d_str,
                    "totalTrips": dm["total_trips"],
                    "onTimePercentage": round(
                        (dm["on_time_trips"] / dm["total_trips"] * 100)
                        if dm["total_trips"]
                        else 0,
                        1,
                    ),
                    "avgDelay": round(dm["total_delay"] / dm["total_trips"], 1)
                    if dm["total_trips"]
                    else 0.0,
                    "totalPassengers": dm["total_passengers"],
                    "fuelConsumption": dm["fuel"],
                    "revenue": dm["revenue"],
                }
            )
            summary_trips += dm["total_trips"]
            summary_on_time += dm["on_time_trips"]
            summary_delay += dm["total_delay"]
            summary_passengers += dm["total_passengers"]
            summary_fuel += dm["fuel"]
            summary_revenue += dm["revenue"]
        else:
            daily.append(
                {
                    "date": d_str,
                    "totalTrips": 0,
                    "onTimePercentage": 0.0,
                    "avgDelay": 0.0,
                    "totalPassengers": 0,
                    "fuelConsumption": 0.0,
                    "revenue": 0.0,
                }
            )
        current_date += timedelta(days=1)

    summary = {
        "totalTrips": summary_trips,
        "onTimePercentage": round(
            (summary_on_time / summary_trips * 100) if summary_trips else 0, 1
        ),
        "avgDelay": round(summary_delay / summary_trips, 1) if summary_trips else 0.0,
        "totalPassengers": summary_passengers,
        "totalFuelConsumption": summary_fuel,
        "totalRevenue": summary_revenue,
    }

    result = {"summary": summary, "daily": daily}

    try:
        await redis_client.setex(cache_key, 60, json.dumps(result))
    except Exception as e:
        logger.warning(f"Failed to write to Redis cache: {e}")

    return result


async def get_filtered_report(
    db: AsyncSession,
    tenant_id: str,
    report_type: str,
    date_from: date,
    date_to: date,
    route_id: str | None = None,
    vehicle_id: str | None = None,
    driver_id: str | None = None,
):
    if report_type == "route":
        route_q = select(Route).where(Route.tenant_id == tenant_id)
        if route_id:
            route_q = route_q.where(Route.id == route_id)
        routes = (await db.execute(route_q)).scalars().all()

        trip_q = (
            select(Trip)
            .options(selectinload(Trip.vehicle))
            .where(
                Trip.tenant_id == tenant_id,
                cast(Trip.created_at, Date) >= date_from,
                cast(Trip.created_at, Date) <= date_to,
            )
        )
        if route_id:
            trip_q = trip_q.where(Trip.route_id == route_id)
        if vehicle_id:
            trip_q = trip_q.where(Trip.vehicle_id == vehicle_id)
        if driver_id:
            trip_q = trip_q.where(Trip.driver_id == driver_id)
        trips = (await db.execute(trip_q)).scalars().all()

        route_stats = {
            r.id: {
                "route": r,
                "trips": [],
                "on_time": 0,
                "duration_sum": 0,
                "duration_count": 0,
                "passengers": 0,
                "capacity": 0,
            }
            for r in routes
        }
        for t in trips:
            if t.route_id in route_stats:
                rs = route_stats[t.route_id]
                rs["trips"].append(t)
                if t.delay <= 0:
                    rs["on_time"] += 1
                if t.actual_end and t.actual_start:
                    rs["duration_sum"] += (
                        t.actual_end - t.actual_start
                    ).total_seconds() / 60.0
                    rs["duration_count"] += 1
                rs["passengers"] += t.passengers
                if t.vehicle:
                    rs["capacity"] += t.vehicle.capacity

        result = []
        for r_id, rs in route_stats.items():
            total = len(rs["trips"])
            result.append(
                RouteReportData(
                    route_id=r_id,
                    route_name=rs["route"].name,
                    on_time_rate=round(
                        (rs["on_time"] / total * 100) if total else 0.0, 1
                    ),
                    avg_trip_duration_minutes=round(
                        (rs["duration_sum"] / rs["duration_count"])
                        if rs["duration_count"]
                        else 0.0,
                        1,
                    ),
                    total_passengers=rs["passengers"],
                    utilisation_percentage=round(
                        (rs["passengers"] / rs["capacity"] * 100)
                        if rs["capacity"]
                        else 0.0,
                        1,
                    ),
                )
            )
        return result

    elif report_type == "daily":
        trip_q = select(Trip).where(
            Trip.tenant_id == tenant_id,
            cast(Trip.created_at, Date) >= date_from,
            cast(Trip.created_at, Date) <= date_to,
        )
        if route_id:
            trip_q = trip_q.where(Trip.route_id == route_id)
        if vehicle_id:
            trip_q = trip_q.where(Trip.vehicle_id == vehicle_id)
        if driver_id:
            trip_q = trip_q.where(Trip.driver_id == driver_id)

        trips = (await db.execute(trip_q)).scalars().all()

        daily_stats = {}
        curr = date_from
        while curr <= date_to:
            daily_stats[curr] = {
                "total": 0,
                "completed": 0,
                "cancelled": 0,
                "passengers": 0,
            }
            curr += timedelta(days=1)

        for t in trips:
            d = (
                t.created_at.date()
                if isinstance(t.created_at, datetime)
                else t.created_at
            )
            if d in daily_stats:
                daily_stats[d]["total"] += 1
                if t.status == "completed":
                    daily_stats[d]["completed"] += 1
                elif t.status == "cancelled":
                    daily_stats[d]["cancelled"] += 1
                daily_stats[d]["passengers"] += t.passengers

        result = []
        for d, st in daily_stats.items():
            result.append(
                DailyReportData(
                    date=d,
                    total_trips=st["total"],
                    completed_trips=st["completed"],
                    cancelled_trips=st["cancelled"],
                    total_passengers=st["passengers"],
                )
            )
        return sorted(result, key=lambda x: x.date)

    elif report_type == "fleet":
        veh_q = select(Vehicle).where(Vehicle.tenant_id == tenant_id)
        if vehicle_id:
            veh_q = veh_q.where(Vehicle.id == vehicle_id)
        vehicles = (await db.execute(veh_q)).scalars().all()

        trip_q = (
            select(Trip)
            .options(selectinload(Trip.route))
            .where(
                Trip.tenant_id == tenant_id,
                cast(Trip.created_at, Date) >= date_from,
                cast(Trip.created_at, Date) <= date_to,
            )
        )
        if route_id:
            trip_q = trip_q.where(Trip.route_id == route_id)
        if vehicle_id:
            trip_q = trip_q.where(Trip.vehicle_id == vehicle_id)
        if driver_id:
            trip_q = trip_q.where(Trip.driver_id == driver_id)
        trips = (await db.execute(trip_q)).scalars().all()

        maint_q = select(MaintenanceRecord).where(
            MaintenanceRecord.tenant_id == tenant_id,
            MaintenanceRecord.scheduled_date >= date_from,
            MaintenanceRecord.scheduled_date <= date_to,
        )
        if vehicle_id:
            maint_q = maint_q.where(MaintenanceRecord.vehicle_id == vehicle_id)
        maintenances = (await db.execute(maint_q)).scalars().all()

        veh_stats = {
            v.id: {"veh": v, "passengers": 0, "capacity": 0, "maint": 0, "km": 0.0}
            for v in vehicles
        }
        for t in trips:
            if t.vehicle_id in veh_stats:
                vs = veh_stats[t.vehicle_id]
                vs["passengers"] += t.passengers
                vs["capacity"] += vs["veh"].capacity
                if t.route and t.status == "completed":
                    vs["km"] += t.route.distance

        for m in maintenances:
            if m.vehicle_id in veh_stats:
                veh_stats[m.vehicle_id]["maint"] += 1

        result = []
        for v_id, vs in veh_stats.items():
            result.append(
                FleetReportData(
                    vehicle_id=v_id,
                    registration_number=vs["veh"].registration_number,
                    utilisation_percentage=round(
                        (vs["passengers"] / vs["capacity"] * 100)
                        if vs["capacity"]
                        else 0.0,
                        1,
                    ),
                    maintenance_events=vs["maint"],
                    total_km=round(vs["km"], 2),
                    status=vs["veh"].status,
                )
            )
        return result

    elif report_type == "driver":
        drv_q = select(Driver).where(Driver.tenant_id == tenant_id)
        if driver_id:
            drv_q = drv_q.where(Driver.id == driver_id)
        drivers = (await db.execute(drv_q)).scalars().all()

        trip_q = select(Trip).where(
            Trip.tenant_id == tenant_id,
            cast(Trip.created_at, Date) >= date_from,
            cast(Trip.created_at, Date) <= date_to,
        )
        if route_id:
            trip_q = trip_q.where(Trip.route_id == route_id)
        if vehicle_id:
            trip_q = trip_q.where(Trip.vehicle_id == vehicle_id)
        if driver_id:
            trip_q = trip_q.where(Trip.driver_id == driver_id)
        trips = (await db.execute(trip_q)).scalars().all()

        drv_stats = {
            d.id: {
                "drv": d,
                "total": 0,
                "completed": 0,
                "on_time": 0,
                "duration_sum": 0,
                "duration_count": 0,
                "passengers": 0,
            }
            for d in drivers
        }
        for t in trips:
            if t.driver_id in drv_stats:
                ds = drv_stats[t.driver_id]
                ds["total"] += 1
                if t.status == "completed":
                    ds["completed"] += 1
                if t.delay <= 0:
                    ds["on_time"] += 1
                if t.actual_end and t.actual_start:
                    ds["duration_sum"] += (
                        t.actual_end - t.actual_start
                    ).total_seconds() / 60.0
                    ds["duration_count"] += 1
                ds["passengers"] += t.passengers

        result = []
        for d_id, ds in drv_stats.items():
            total = ds["total"]
            result.append(
                DriverReportData(
                    driver_id=d_id,
                    driver_name=ds["drv"].name,
                    trips_completed=ds["completed"],
                    on_time_rate=round(
                        (ds["on_time"] / total * 100) if total else 0.0, 1
                    ),
                    avg_trip_duration_minutes=round(
                        (ds["duration_sum"] / ds["duration_count"])
                        if ds["duration_count"]
                        else 0.0,
                        1,
                    ),
                    total_passengers=ds["passengers"],
                )
            )
        return result
    return []


async def get_passenger_report(
    db: AsyncSession,
    tenant_id: str,
    passenger_id: str,
    date_from: date,
    date_to: date,
) -> PassengerReportResponse:
    from fastapi import HTTPException

    user_q = select(User).where(
        User.id == passenger_id,
        User.tenant_id == tenant_id,
        User.role == "passenger",
        User.is_deleted.is_(False),
    )
    user_result = await db.execute(user_q)
    user = user_result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="Passenger not found in this tenant.",
        )

    # Phase 12 boarding records do not exist yet — return a graceful placeholder.
    return PassengerReportResponse(
        passenger_id=str(passenger_id),
        passenger_name=user.full_name or user.email,
        date_from=str(date_from),
        date_to=str(date_to),
        generated_at=datetime.utcnow().isoformat(),
        message=(
            "Trip association records are not yet available. "
            "This report will be populated once passenger boarding tracking is enabled."
        ),
        data=[],
    )
