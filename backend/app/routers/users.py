from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_tenant, get_current_user, require_role
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.common import PaginatedResponse, APIResponse, Meta, MessageResponse
from app.schemas.user import UserCreate, UserInviteAccept, UserRead, UserUpdate
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
    summary="List users",
    description="Returns a paginated list of users in the current tenant. Optionally filter by role.",
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
    dependencies=[Depends(require_role("superadmin", "admin"))],
    summary="Create a user",
    description="Invites a new user into the current tenant. Returns 409 if the email is already taken.",
)
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
):
    user = await user_service.create_user(db, data, tenant.id, current_user, tenant)
    await db.commit()
    return APIResponse(data=UserRead.model_validate(user))


@router.get(
    "/{id}",
    response_model=APIResponse[UserRead],
    summary="Get a user",
    description="Returns a single user. Admins may fetch any user; other roles may only fetch their own profile.",
)
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


@router.patch(
    "/{id}",
    response_model=APIResponse[UserRead],
    summary="Update a user",
    description="Partially updates a user's profile. Users may edit their own record; admins may edit any.",
)
async def update_user(
    id: str,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
):
    user = await user_service.update_user(db, id, data, tenant.id, current_user)
    await db.commit()
    return APIResponse(data=UserRead.model_validate(user))


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("superadmin", "admin"))],
    summary="Delete a user",
    description="Soft-deletes a user from the tenant. Requires admin role.",
)
async def delete_user(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
):
    await user_service.delete_user(db, id, tenant.id, current_user)
    await db.commit()


@router.post(
    "/accept-invite",
    response_model=APIResponse[MessageResponse],
    summary="Accept a staff invitation",
    description=(
        "Sets the password for an invited user and activates their account. "
        "The token is from the invitation email link. No authentication required."
    ),
)
async def accept_invite(
    data: UserInviteAccept,
    db: AsyncSession = Depends(get_db),
):
    await user_service.accept_invitation(db, data)
    await db.commit()
    return APIResponse(
        data=MessageResponse(message="Account activated. You can now log in.")
    )
