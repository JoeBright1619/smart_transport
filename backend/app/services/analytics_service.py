import json
import logging
from datetime import date, datetime, timedelta
from typing import Any

import redis.asyncio as redis
from sqlalchemy import select, func, case, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.analytics import AnalyticsRecord
from app.models.trip import Trip

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
