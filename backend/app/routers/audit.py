from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_tenant, get_current_user, require_role
from app.models.audit_log import AuditLog
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.audit import AuditLogRead
from app.schemas.common import Meta, PaginatedResponse
from app.services import audit_service

router = APIRouter(prefix="/api/v1/audit-logs", tags=["audit"])


def _to_read_model(log: AuditLog) -> AuditLogRead:
    return AuditLogRead(
        id=log.id,
        user_id=log.user_id,
        tenant_id=log.tenant_id,
        resource_type=log.entity_type,
        resource_id=log.entity_id,
        action=log.action_type,
        metadata=log.metadata_,
        created_at=log.created_at,
    )


@router.get(
    "",
    response_model=PaginatedResponse[AuditLogRead],
    dependencies=[Depends(require_role("admin"))],
    summary="List audit logs",
    description="Returns tenant audit logs ordered by newest first.",
)
async def list_audit_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    action: str | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
):
    logs, total = await audit_service.list_logs(
        db,
        tenant.id,
        page=page,
        page_size=page_size,
        action=action,
        resource_type=resource_type,
    )
    return PaginatedResponse(
        data=[_to_read_model(log) for log in logs],
        meta=Meta(total=total, page=page, pageSize=page_size),
    )
