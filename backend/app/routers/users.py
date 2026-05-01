from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_tenant, get_current_user, require_role
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.common import PaginatedResponse, APIResponse, Meta
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/api/v1/users", tags=["users"])


def _error_detail(code: str, message: str) -> dict:
    return {
        "data": None,
        "meta": None,
        "error": {
            "code": code,
            "message": message,
        },
    }


@router.get(
    "",
    response_model=PaginatedResponse[UserRead],
    dependencies=[Depends(require_role("superadmin", "admin"))],
)
async def list_users(
    role: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    users, total = await user_service.get_users(db, tenant.id, role, page, page_size)
    return PaginatedResponse(
        data=[UserRead.model_validate(u) for u in users],
        meta=Meta(total=total, page=page, pageSize=page_size),
    )


@router.post(
    "",
    response_model=APIResponse[UserRead],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin"))],
)
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
):
    async with db.begin():
        user = await user_service.create_user(db, data, tenant.id, current_user)
        return APIResponse(data=UserRead.model_validate(user))


@router.get("/{id}", response_model=APIResponse[UserRead])
async def get_user(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
):
    if current_user.role not in ["admin", "superadmin"] and current_user.id != id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_error_detail("FORBIDDEN", "Cannot view other users"),
        )

    user = await user_service.get_user_by_id(db, id, tenant.id)
    return APIResponse(data=UserRead.model_validate(user))


@router.patch("/{id}", response_model=APIResponse[UserRead])
async def update_user(
    id: str,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
):
    async with db.begin():
        user = await user_service.update_user(db, id, data, tenant.id, current_user)
        return APIResponse(data=UserRead.model_validate(user))


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("admin"))],
)
async def delete_user(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
):
    async with db.begin():
        await user_service.delete_user(db, id, tenant.id, current_user)
