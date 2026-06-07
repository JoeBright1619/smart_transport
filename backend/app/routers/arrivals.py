from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_tenant, get_current_user, require_role
from app.models.tenant import Tenant
from app.schemas.arrival import ArrivalRead, PublicArrivalRead
from app.schemas.common import APIResponse
from app.services import arrival_service

router = APIRouter(prefix="/api/v1/arrivals", tags=["arrivals"])


@router.get(
    "/public",
    response_model=APIResponse[list[PublicArrivalRead]],
    summary="Get cross-tenant arrivals for a stop (passenger)",
    description=(
        "Returns ETA estimates from all operators for the given stop. "
        "Each result includes the operator company name. Requires passenger role."
    ),
)
async def get_public_arrivals(
    stop_id: str = Query(alias="stop_id"),
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(require_role("passenger")),
) -> APIResponse[list[PublicArrivalRead]]:
    arrivals = await arrival_service.get_cross_tenant_arrivals(db, stop_id)
    return APIResponse(data=arrivals)


@router.get(
    "",
    response_model=APIResponse[list[ArrivalRead]],
    summary="Get predicted arrivals for a stop",
    description=(
        "Returns ETA estimates for all active vehicles currently heading toward the given stop. "
        "ETAs are calculated along the ordered route stops from each vehicle's current route segment."
    ),
)
async def get_arrivals(
    stop_id: str = Query(alias="stopId"),
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
    _current_user=Depends(get_current_user),
) -> APIResponse[list[ArrivalRead]]:
    arrivals = await arrival_service.get_arrivals_for_stop(db, tenant.id, stop_id)
    return APIResponse(data=arrivals)
