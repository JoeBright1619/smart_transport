"""Tests for the staff invitation flow (Task 11.1).

Covers:
  - POST /api/v1/users  (invitation mode — no password provided)
  - POST /api/v1/users/accept-invite
  - Role-hierarchy enforcement (equal rank allowed, higher rank blocked)
  - Email uniqueness exemption for soft-deleted users
"""

from __future__ import annotations

from datetime import timedelta
from hashlib import sha256

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from tests.conftest import auth_headers


# ---------------------------------------------------------------------------
# Module-level fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def make_invited_user(make_user, db: AsyncSession):
    """Create a user with status='invited' and a matching invite token.

    Returns (user, raw_token) so tests can call accept-invite directly.
    """

    async def _create(*, tenant_id: str, role: str = "operator"):
        user = await make_user(tenant_id=tenant_id, role=role, status="invited")
        token = create_access_token(
            {"sub": user.id, "type": "invite"},
            expires_delta=timedelta(hours=48),
        )
        user.invitation_token_hash = sha256(token.encode()).hexdigest()
        await db.flush()
        return user, token

    return _create


# ---------------------------------------------------------------------------
# POST /api/v1/users — invitation mode (no password)
# ---------------------------------------------------------------------------


async def test_invite_without_password_returns_201_with_invited_status(
    client, admin_user
):
    r = await client.post(
        "/api/v1/users",
        json={
            "full_name": "Invited User",
            "email": "invite@test.local",
            "role": "operator",
        },
        headers=auth_headers(admin_user),
    )
    assert r.status_code == 201
    data = r.json()["data"]
    assert data["email"] == "invite@test.local"
    assert data["status"] == "invited"


async def test_admin_can_invite_another_admin(client, admin_user):
    """Equal-rank creation is allowed — an admin can invite another admin."""
    r = await client.post(
        "/api/v1/users",
        json={
            "full_name": "Second Admin",
            "email": "admin2@test.local",
            "role": "admin",
        },
        headers=auth_headers(admin_user),
    )
    assert r.status_code == 201
    assert r.json()["data"]["role"] == "admin"


async def test_admin_cannot_invite_superadmin(client, admin_user):
    """'superadmin' is not a valid TenantUserRole — rejected at schema validation (422)
    before the service-level rank check even runs, which is stricter."""
    r = await client.post(
        "/api/v1/users",
        json={
            "full_name": "Escalation",
            "email": "esc@test.local",
            "role": "superadmin",
        },
        headers=auth_headers(admin_user),
    )
    assert r.status_code == 422


async def test_operator_cannot_invite_anyone(client, operator_user):
    r = await client.post(
        "/api/v1/users",
        json={"full_name": "X", "email": "x@test.local", "role": "dispatcher"},
        headers=auth_headers(operator_user),
    )
    assert r.status_code == 403


async def test_invite_without_auth_returns_401(client):
    r = await client.post(
        "/api/v1/users",
        json={"full_name": "X", "email": "x@test.local", "role": "dispatcher"},
    )
    assert r.status_code == 401


async def test_invite_missing_email_returns_422(client, admin_user):
    r = await client.post(
        "/api/v1/users",
        json={"full_name": "X", "role": "dispatcher"},
        headers=auth_headers(admin_user),
    )
    assert r.status_code == 422


async def test_invite_invalid_email_returns_422(client, admin_user):
    r = await client.post(
        "/api/v1/users",
        json={"full_name": "New Staff", "email": "not-an-email", "role": "dispatcher"},
        headers=auth_headers(admin_user),
    )
    assert r.status_code == 422


async def test_invite_duplicate_active_email_returns_409(
    client, admin_user, make_user, tenant
):
    existing = await make_user(
        tenant_id=tenant.id, email="taken@test.local", role="operator"
    )
    r = await client.post(
        "/api/v1/users",
        json={"full_name": "Dup", "email": existing.email, "role": "dispatcher"},
        headers=auth_headers(admin_user),
    )
    assert r.status_code == 409


async def test_invite_reuses_soft_deleted_email(
    client, admin_user, make_user, db, tenant
):
    """Soft-deleting a user must free their email for future invitations."""
    existing = await make_user(
        tenant_id=tenant.id, email="recycled@test.local", role="operator"
    )
    existing.is_deleted = True
    await db.flush()

    r = await client.post(
        "/api/v1/users",
        json={
            "full_name": "New Person",
            "email": "recycled@test.local",
            "role": "dispatcher",
        },
        headers=auth_headers(admin_user),
    )
    assert r.status_code == 201


# ---------------------------------------------------------------------------
# POST /api/v1/users/accept-invite
# ---------------------------------------------------------------------------


async def test_accept_invite_happy_path(client, make_invited_user, tenant):
    _, token = await make_invited_user(tenant_id=tenant.id)
    r = await client.post(
        "/api/v1/users/accept-invite",
        json={"token": token, "new_password": "NewSecurePass1!"},
    )
    assert r.status_code == 200
    assert "activated" in r.json()["data"]["message"].lower()


async def test_accept_invite_sets_user_active(client, make_invited_user, tenant, db):
    user, token = await make_invited_user(tenant_id=tenant.id)
    await client.post(
        "/api/v1/users/accept-invite",
        json={"token": token, "new_password": "NewSecurePass1!"},
    )
    await db.refresh(user)
    assert user.status == "active"
    assert user.invitation_token_hash is None


async def test_accept_invite_invalid_token_returns_400(client):
    r = await client.post(
        "/api/v1/users/accept-invite",
        json={"token": "not.a.jwt", "new_password": "NewSecurePass1!"},
    )
    assert r.status_code == 400


async def test_accept_invite_login_token_rejected(client, make_user, tenant):
    """A normal login JWT must not be accepted as an invite token."""
    user = await make_user(tenant_id=tenant.id, role="operator", status="invited")
    login_token = create_access_token(
        {"userId": user.id, "tenantId": tenant.id, "role": user.role}
    )
    r = await client.post(
        "/api/v1/users/accept-invite",
        json={"token": login_token, "new_password": "NewSecurePass1!"},
    )
    assert r.status_code == 400


async def test_accept_invite_already_accepted_returns_409(
    client, make_invited_user, tenant
):
    _, token = await make_invited_user(tenant_id=tenant.id)
    # First acceptance activates the account
    await client.post(
        "/api/v1/users/accept-invite",
        json={"token": token, "new_password": "NewSecurePass1!"},
    )
    # Second attempt with the same token must be rejected
    r = await client.post(
        "/api/v1/users/accept-invite",
        json={"token": token, "new_password": "AnotherPass1!"},
    )
    assert r.status_code == 409


async def test_accept_invite_hash_mismatch_returns_400(
    client, make_invited_user, tenant
):
    """A fresh token for the same user (different expiry → different hash) must be rejected."""
    user, _stored_token = await make_invited_user(tenant_id=tenant.id)
    # Generate a second valid invite JWT — different expiry means different bytes → hash won't match
    fresh_token = create_access_token(
        {"sub": user.id, "type": "invite"},
        expires_delta=timedelta(hours=24),
    )
    r = await client.post(
        "/api/v1/users/accept-invite",
        json={"token": fresh_token, "new_password": "NewSecurePass1!"},
    )
    assert r.status_code == 400


async def test_accept_invite_short_password_returns_422(
    client, make_invited_user, tenant
):
    _, token = await make_invited_user(tenant_id=tenant.id)
    r = await client.post(
        "/api/v1/users/accept-invite",
        json={"token": token, "new_password": "short"},
    )
    assert r.status_code == 422
