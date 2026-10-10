from fastapi import APIRouter, Depends

from app.core.dependencies import get_tenant_or_service
from app.models.tenant import Tenant
from app.schemas.common import APIResponse
from app.schemas.service import WhoAmIResponse

router = APIRouter(prefix="/api/v1/service", tags=["service"])


@router.get(
    "/whoami",
    response_model=APIResponse[WhoAmIResponse],
    summary="Identify the calling service's tenant",
    description=(
        "Returns the tenant associated with the caller's service token. "
        "Used by external services to discover their tenant at startup."
    ),
)
async def whoami(
    tenant: Tenant = Depends(get_tenant_or_service()),
) -> APIResponse[WhoAmIResponse]:
    return APIResponse(
        data=WhoAmIResponse(tenant_id=tenant.id, tenant_name=tenant.name)
    )
