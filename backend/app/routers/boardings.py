from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_role
from app.models.user import User
from app.schemas.boarding import BoardingRecordRead, PassengerTripRead
from app.schemas.common import Meta, PaginatedResponse
from app.services import boarding_service

router = APIRouter(prefix="/api/v1/boardings", tags=["boardings"])


@router.get(
    "",
    response_model=PaginatedResponse[BoardingRecordRead],
    dependencies=[Depends(require_role("superadmin", "admin", "operator"))],
    summary="List boarding records",
)
async def list_boardings(
    trip_id: str | None = Query(default=None, alias="tripId"),
    stop_id: str | None = Query(default=None, alias="stopId"),
    date_from: date | None = Query(default=None, alias="dateFrom"),
    date_to: date | None = Query(default=None, alias="dateTo"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100, alias="pageSize"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("superadmin", "admin", "operator")),
) -> PaginatedResponse[BoardingRecordRead]:
    tenant_id = current_user.tenant_id or ""
    records, total = await boarding_service.list_boardings(
        db, tenant_id, trip_id, stop_id, date_from, date_to, page, page_size
    )
    return PaginatedResponse(
        data=records,
        meta=Meta(total=total, page=page, pageSize=page_size),
    )


@router.get(
    "/me",
    response_model=PaginatedResponse[PassengerTripRead],
    summary="Get my recorded boardings",
)
async def get_my_boardings(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100, alias="pageSize"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("passenger")),
) -> PaginatedResponse[PassengerTripRead]:
    records, total = await boarding_service.list_my_boardings(
        db, current_user.id, page, page_size
    )
    return PaginatedResponse(
        data=records,
        meta=Meta(total=total, page=page, pageSize=page_size),
    )
