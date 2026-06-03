from datetime import date, timedelta, datetime
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_tenant, require_role
from app.models.tenant import Tenant
from app.schemas.common import APIResponse
from app.schemas.analytics import (
    AnalyticsResponseData,
    FilteredReportResponse,
    PassengerReportResponse,
)
from app.services import analytics_service

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get(
    "",
    response_model=APIResponse[AnalyticsResponseData],
    dependencies=[Depends(require_role("admin", "operator"))],
    summary="Get fleet analytics",
    description=(
        "Returns aggregated KPIs and a per-day breakdown for the given date window. "
        "Defaults to the last 7 days when `from`/`to` are omitted."
    ),
)
async def get_analytics(
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    if to_date is None:
        to_date = date.today()
    if from_date is None:
        from_date = to_date - timedelta(days=6)

    data = await analytics_service.get_analytics(db, tenant.id, from_date, to_date)
    return APIResponse(data=AnalyticsResponseData.model_validate(data))


@router.get(
    "/report",
    response_model=APIResponse[FilteredReportResponse],
    dependencies=[Depends(require_role("admin", "operator"))],
    summary="Get filtered reports",
)
async def get_filtered_analytics_report(
    report_type: Literal["route", "daily", "fleet", "driver"] = Query(...),
    route_id: str | None = Query(None),
    vehicle_id: str | None = Query(None),
    driver_id: str | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    if date_to is None:
        date_to = date.today()
    if date_from is None:
        date_from = date_to - timedelta(days=29)

    data = await analytics_service.get_filtered_report(
        db=db,
        tenant_id=tenant.id,
        report_type=report_type,
        date_from=date_from,
        date_to=date_to,
        route_id=route_id,
        vehicle_id=vehicle_id,
        driver_id=driver_id,
    )

    return APIResponse(
        data=FilteredReportResponse(
            report_type=report_type,
            filters_applied={
                "route_id": route_id,
                "vehicle_id": vehicle_id,
                "driver_id": driver_id,
                "date_from": date_from,
                "date_to": date_to,
            },
            generated_at=datetime.utcnow(),
            data=data,
        )
    )


@router.get(
    "/passenger-report",
    response_model=APIResponse[PassengerReportResponse],
    dependencies=[Depends(require_role("admin", "dispatcher"))],
    summary="Get passenger trip history report",
    description=(
        "Returns the trip history for a specific passenger. "
        "Requires Phase 12 boarding tracking to be enabled for populated results."
    ),
)
async def get_passenger_trip_report(
    passenger_id: str = Query(..., description="ID of the passenger user"),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    if date_to is None:
        date_to = date.today()
    if date_from is None:
        date_from = date_to - timedelta(days=29)

    data = await analytics_service.get_passenger_report(
        db=db,
        tenant_id=tenant.id,
        passenger_id=passenger_id,
        date_from=date_from,
        date_to=date_to,
    )
    return APIResponse(data=data)
