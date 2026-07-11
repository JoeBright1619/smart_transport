import math
from typing import Sequence

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.route import Route, Stop, RouteStop
from app.models.trip import Trip
from app.schemas.route import RouteCreate, RouteUpdate
from app.services import audit_service


EARTH_RADIUS_M = 6_371_000
STOP_COORDINATE_CONFLICT_METERS = 10


def _error_detail(code: str, message: str) -> dict:
    return {
        "data": None,
        "meta": None,
        "error": {
            "code": code,
            "message": message,
        },
    }


def _distance_meters(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_M * c


async def list_stops(db: AsyncSession, tenant_id: str) -> Sequence[Stop]:
    result = await db.execute(
        select(Stop)
        .where(Stop.tenant_id == tenant_id, Stop.is_deleted.is_(False))
        .order_by(Stop.name.asc())
    )
    return result.scalars().all()


async def list_all_stops(db: AsyncSession) -> Sequence[Stop]:
    result = await db.execute(
        select(Stop).where(Stop.is_deleted.is_(False)).order_by(Stop.name.asc())
    )
    return result.scalars().all()


async def create_stop(db: AsyncSession, data, tenant_id: str) -> Stop:
    existing_stops = await list_stops(db, tenant_id)
    normalized_name = data.name.strip().casefold()

    for stop in existing_stops:
        if stop.name.casefold() == normalized_name:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=_error_detail(
                    "STOP_NAME_CONFLICT", "A stop with this name already exists"
                ),
            )

        if (
            _distance_meters(data.lat, data.lng, stop.lat, stop.lng)
            <= STOP_COORDINATE_CONFLICT_METERS
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=_error_detail(
                    "STOP_COORDINATE_CONFLICT",
                    "A stop already exists within 10 meters of these coordinates",
                ),
            )

    stop = Stop(tenant_id=tenant_id, name=data.name.strip(), lat=data.lat, lng=data.lng)
    db.add(stop)
    await db.flush()
    return stop


async def _get_route_stops_by_id(
    db: AsyncSession,
    tenant_id: str,
    stop_ids: Sequence[str],
) -> dict[str, Stop]:
    unique_stop_ids = list(dict.fromkeys(stop_ids))
    result = await db.execute(
        select(Stop).where(
            Stop.id.in_(unique_stop_ids),
            Stop.tenant_id == tenant_id,
            Stop.is_deleted.is_(False),
        )
    )
    stops = {stop.id: stop for stop in result.scalars().all()}

    missing_ids = [stop_id for stop_id in unique_stop_ids if stop_id not in stops]
    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_error_detail("NOT_FOUND", "One or more stops were not found"),
        )

    return stops


async def _replace_route_stops(
    db: AsyncSession,
    route_id: str,
    tenant_id: str,
    stops_data: Sequence,
) -> None:
    stop_ids = [
        stop_data.stop_id if hasattr(stop_data, "stop_id") else stop_data["stop_id"]
        for stop_data in stops_data
    ]
    if len(stop_ids) != len(set(stop_ids)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_error_detail(
                "CONFLICT", "A route cannot include the same stop twice"
            ),
        )

    await _get_route_stops_by_id(db, tenant_id, stop_ids)
    await db.execute(delete(RouteStop).where(RouteStop.route_id == route_id))
    await db.flush()

    for stop_data in stops_data:
        stop_id = (
            stop_data.stop_id if hasattr(stop_data, "stop_id") else stop_data["stop_id"]
        )
        order = stop_data.order if hasattr(stop_data, "order") else stop_data["order"]
        db.add(RouteStop(route_id=route_id, stop_id=stop_id, stop_order=order))


async def get_routes(
    db: AsyncSession,
    tenant_id: str,
    is_active: bool | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[Sequence[Route], int]:
    query = select(Route).where(
        Route.tenant_id == tenant_id, Route.is_deleted.is_(False)
    )

    if is_active is not None:
        query = query.where(Route.is_active == is_active)

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    query = (
        query.options(selectinload(Route.route_stops).selectinload(RouteStop.stop))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .order_by(Route.created_at.desc())
    )
    result = await db.execute(query)
    routes = result.scalars().all()

    return routes, total


async def get_route_by_id(db: AsyncSession, route_id: str, tenant_id: str) -> Route:
    result = await db.execute(
        select(Route)
        .options(selectinload(Route.route_stops).selectinload(RouteStop.stop))
        .where(
            Route.id == route_id,
            Route.tenant_id == tenant_id,
            Route.is_deleted.is_(False),
        )
    )
    route = result.scalar_one_or_none()
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_error_detail("NOT_FOUND", "Route not found"),
        )
    return route


async def ensure_route_active(db: AsyncSession, route_id: str, tenant_id: str) -> Route:
    """Return the route only if it exists and is active; else 404/409.

    Single guard used wherever a route is put to work (vehicle route assignment, trip
    dispatch) so a disabled route can never be assigned or dispatched.
    """
    route = (
        await db.execute(
            select(Route).where(
                Route.id == route_id,
                Route.tenant_id == tenant_id,
                Route.is_deleted.is_(False),
            )
        )
    ).scalar_one_or_none()
    if route is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_error_detail("NOT_FOUND", "Route not found"),
        )
    if not route.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_error_detail(
                "ROUTE_INACTIVE",
                "Route is disabled — enable it before assigning or dispatching",
            ),
        )
    return route


async def create_route(
    db: AsyncSession, data: RouteCreate, tenant_id: str, current_user_id: str
) -> Route:
    existing = await db.execute(
        select(Route).where(
            Route.number == data.number,
            Route.tenant_id == tenant_id,
            Route.is_deleted.is_(False),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_error_detail("CONFLICT", "Route with this number already exists"),
        )

    route = Route(
        tenant_id=tenant_id,
        name=data.name,
        number=data.number,
        distance=data.distance,
        duration=data.duration,
        color=data.color,
    )
    db.add(route)
    await db.flush()

    await _replace_route_stops(db, route.id, tenant_id, data.stops)

    await db.flush()
    await audit_service.log(db, current_user_id, tenant_id, "Route", route.id, "create")

    return await get_route_by_id(db, route.id, tenant_id)


async def update_route(
    db: AsyncSession,
    route_id: str,
    data: RouteUpdate,
    tenant_id: str,
    current_user_id: str,
) -> Route:
    route = await get_route_by_id(db, route_id, tenant_id)

    update_data = data.model_dump(exclude_unset=True)

    if "name" in update_data:
        route.name = update_data["name"]
    if "number" in update_data and update_data["number"] != route.number:
        existing = await db.execute(
            select(Route).where(
                Route.number == update_data["number"],
                Route.tenant_id == tenant_id,
                Route.id != route.id,
                Route.is_deleted.is_(False),
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=_error_detail(
                    "CONFLICT", "Route with this number already exists"
                ),
            )
        route.number = update_data["number"]
    if "distance" in update_data:
        route.distance = update_data["distance"]
    if "duration" in update_data:
        route.duration = update_data["duration"]
    if "is_active" in update_data:
        route.is_active = update_data["is_active"]
    if "color" in update_data:
        route.color = update_data["color"]

    if "stops" in update_data:
        await _replace_route_stops(db, route.id, tenant_id, update_data["stops"])

    await db.flush()
    await audit_service.log(
        db,
        current_user_id,
        tenant_id,
        "Route",
        route.id,
        "update",
        metadata=update_data,
    )

    return await get_route_by_id(db, route.id, tenant_id)


async def delete_route(
    db: AsyncSession, route_id: str, tenant_id: str, current_user_id: str
) -> None:
    route = await get_route_by_id(db, route_id, tenant_id)

    active_trips_query = select(Trip).where(
        Trip.route_id == route_id,
        Trip.status.in_(["active", "scheduled"]),
        Trip.is_deleted.is_(False),
    )
    active_trips_result = await db.execute(active_trips_query)
    if active_trips_result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_error_detail(
                "CONFLICT", "Cannot delete route with active or scheduled trips"
            ),
        )

    route.is_deleted = True
    await db.flush()
    await audit_service.log(
        db, current_user_id, tenant_id, "Route", route.id, "soft_delete"
    )
