from typing import Sequence

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.route import Route, Stop, RouteStop
from app.models.trip import Trip
from app.schemas.route import RouteCreate, RouteUpdate
from app.services import audit_service


def _error_detail(code: str, message: str) -> dict:
    return {
        "data": None,
        "meta": None,
        "error": {
            "code": code,
            "message": message,
        },
    }


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

    for stop_data in data.stops:
        stop = Stop(
            tenant_id=tenant_id,
            name=stop_data.name,
            lat=stop_data.lat,
            lng=stop_data.lng,
        )
        db.add(stop)
        await db.flush()

        route_stop = RouteStop(
            route_id=route.id,
            stop_id=stop.id,
            stop_order=stop_data.order,
        )
        db.add(route_stop)

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
    if "is_active" in update_data:
        route.is_active = update_data["is_active"]
    if "color" in update_data:
        route.color = update_data["color"]

    if "stops" in update_data:
        for rs in list(route.route_stops):
            db.delete(rs.stop)
            db.delete(rs)

        await db.flush()

        for stop_data in update_data["stops"]:
            stop = Stop(
                tenant_id=tenant_id,
                name=stop_data["name"],
                lat=stop_data["lat"],
                lng=stop_data["lng"],
            )
            db.add(stop)
            await db.flush()

            route_stop = RouteStop(
                route_id=route.id,
                stop_id=stop.id,
                stop_order=stop_data["order"],
            )
            db.add(route_stop)

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
