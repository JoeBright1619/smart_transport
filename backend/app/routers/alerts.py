from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_tenant, require_role
from app.models.tenant import Tenant
from app.schemas.common import PaginatedResponse, APIResponse, Meta
from app.schemas.alert import AlertRead
from app.services import alert_service

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


@router.get(
    "",
    response_model=PaginatedResponse[AlertRead],
    dependencies=[Depends(require_role("admin", "operator", "dispatcher"))],
    summary="List alerts",
    description="Returns a paginated list of system alerts. Filter by severity, type, or acknowledgement status.",
)
async def list_alerts(
    severity: str | None = Query(default=None),
    type_filter: str | None = Query(default=None, alias="type"),
    is_acknowledged: bool | None = Query(default=None, alias="isAcknowledged"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    alerts, total = await alert_service.get_alerts(
        db, tenant.id, severity, type_filter, is_acknowledged, page, page_size
    )
    return PaginatedResponse(
        data=[AlertRead.model_validate(a) for a in alerts],
        meta=Meta(total=total, page=page, pageSize=page_size),
    )


@router.post(
    "/{id}/acknowledge",
    response_model=APIResponse[AlertRead],
    dependencies=[Depends(require_role("admin", "operator", "dispatcher"))],
    summary="Acknowledge an alert",
    description="Marks an alert as acknowledged. Idempotent — acknowledging an already-acknowledged alert is a no-op.",
)
async def acknowledge_alert(
    id: str,
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    alert = await alert_service.acknowledge_alert(db, id, tenant.id)
    await db.commit()
    return APIResponse(data=AlertRead.model_validate(alert))
