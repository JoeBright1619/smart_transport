from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_tenant, require_role
from app.models.tenant import Tenant
from app.schemas.common import APIResponse
from app.schemas.analytics import AnalyticsResponseData
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
