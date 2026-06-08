from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_role
from app.models.user import User
from app.schemas.common import APIResponse, Meta, PaginatedResponse
from app.schemas.passenger import (
    PassengerListItem,
    PassengerNotification,
    PassengerProfileRead,
    PassengerProfileUpdate,
    PassengerStatsRead,
)
from app.services import passenger_service, passenger_stats_service

router = APIRouter(prefix="/api/v1/passengers", tags=["passengers"])


@router.get(
    "/me",
    response_model=APIResponse[PassengerProfileRead],
    summary="Get my passenger profile",
    description="Returns the logged-in passenger's profile with resolved route and stop names.",
)
async def get_my_profile(
    current_user: User = Depends(require_role("passenger")),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PassengerProfileRead]:
    profile = await passenger_service.get_profile(db, current_user)
    await db.commit()
    return APIResponse(data=profile)


@router.get(
    "/me/stats",
    response_model=APIResponse[PassengerStatsRead],
    summary="Get my journey statistics",
    description="Returns trip counts, top routes, favourite stop, and weekly breakdown.",
)
async def get_my_stats(
    current_user: User = Depends(require_role("passenger")),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PassengerStatsRead]:
    stats = await passenger_stats_service.get_passenger_stats(db, current_user.id)
    return APIResponse(data=stats)


@router.patch(
    "/me",
    response_model=APIResponse[PassengerProfileRead],
    summary="Update my passenger profile",
    description="Updates phone, preferred routes/stops, and notification preferences.",
)
async def update_my_profile(
    data: PassengerProfileUpdate,
    current_user: User = Depends(require_role("passenger")),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PassengerProfileRead]:
    profile = await passenger_service.update_profile(db, current_user, data)
    await db.commit()
    return APIResponse(data=profile)


@router.get(
    "/me/notifications",
    response_model=APIResponse[list[PassengerNotification]],
    summary="Get notifications for favourite stops",
    description="Returns buses approaching the passenger's favourite stops. Empty list if none are approaching.",
)
async def get_my_notifications(
    current_user: User = Depends(require_role("passenger")),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[list[PassengerNotification]]:
    notifications = await passenger_service.get_passenger_notifications(
        db, current_user
    )
    return APIResponse(data=notifications)


@router.get(
    "",
    response_model=PaginatedResponse[PassengerListItem],
    dependencies=[Depends(require_role("superadmin", "admin"))],
    summary="List all passengers",
    description="Returns a paginated list of all passenger accounts with trip counts.",
)
async def list_passengers(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[PassengerListItem]:
    passengers, total = await passenger_service.list_passengers(db, page, page_size)
    return PaginatedResponse(
        data=[PassengerListItem.model_validate(p) for p in passengers],
        meta=Meta(total=total, page=page, pageSize=page_size),
    )
