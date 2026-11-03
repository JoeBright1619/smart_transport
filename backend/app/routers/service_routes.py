"""Tenant-agnostic route endpoints for cross-tenant consumers.

Mirrors the /api/v1/service/vehicles pattern (Task 3.0): universal
service token or superadmin JWT, `vehicles:read_universal` scope. Used
by passenger_service to fetch route stops for position events whose
routes may belong to any tenant.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import Principal, require_superadmin_or_universal_service
from app.schemas.common import APIResponse
from app.schemas.route import RouteRead
from app.services import route_service

router = APIRouter(prefix="/api/v1/service/routes", tags=["service"])

_UNIVERSAL_SCOPE = "vehicles:read_universal"


@router.get(
    "/{id}",
    response_model=APIResponse[RouteRead],
    summary="Get a route across tenants",
    description=(
        "Returns a single route with all of its ordered stops, regardless "
        "of tenant. Auth: superadmin JWT, or a universal service token "
        "scoped `vehicles:read_universal`."
    ),
)
async def get_service_route(
    id: str,
    db: AsyncSession = Depends(get_db),
    _: Principal = Depends(
        require_superadmin_or_universal_service(required_scope=_UNIVERSAL_SCOPE)
    ),
) -> APIResponse[RouteRead]:
    route = await route_service.get_route_by_id_any_tenant(db, id)
    return APIResponse(data=RouteRead.model_validate(route))
