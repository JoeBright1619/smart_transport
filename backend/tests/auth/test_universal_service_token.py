"""Tests for universal (tenant-agnostic) service tokens.

A universal token is a ServiceToken row with tenant_id IS NULL and a
*_universal scope. It authenticates as Principal(kind="universal_service")
on endpoints that declare require_superadmin_or_universal_service.
"""

from __future__ import annotations

from tests.conftest import auth_headers


async def test_universal_token_grants_passenger_pool(
    client, make_service_token, make_user
):
    p = await make_user(tenant_id=None, role="passenger")
    _, plaintext = await make_service_token(
        universal=True, scopes="passengers:read_universal"
    )

    r = await client.get("/api/v1/passengers", headers={"X-Service-Token": plaintext})
    assert r.status_code == 200
    assert p.id in {item["id"] for item in r.json()["data"]}


async def test_universal_token_missing_scope_rejected(client, make_service_token):
    _, plaintext = await make_service_token(universal=True, scopes="vehicles:read")
    r = await client.get("/api/v1/passengers", headers={"X-Service-Token": plaintext})
    assert r.status_code == 403


async def test_universal_token_not_rejected_on_wrong_path(client, make_service_token):
    # Universal token has passengers scope, not vehicles scope, and does not
    # go through get_tenant_or_service. /vehicles must reject it.
    _, plaintext = await make_service_token(
        universal=True, scopes="passengers:read_universal"
    )
    r = await client.get("/api/v1/vehicles", headers={"X-Service-Token": plaintext})
    assert r.status_code == 403


async def test_tenant_bound_token_rejected_on_universal_endpoint(
    client, make_service_token, tenant
):
    # A tenant-bound token must not be silently upgraded to universal by
    # carrying the universal scope.
    _, plaintext = await make_service_token(
        tenant_id=tenant.id, scopes="passengers:read_universal"
    )
    r = await client.get("/api/v1/passengers", headers={"X-Service-Token": plaintext})
    assert r.status_code == 403


async def test_tenant_bound_token_still_works_on_tenant_endpoints(
    client, make_service_token, tenant
):
    # Regression: get_tenant_or_service is unchanged.
    _, plaintext = await make_service_token(tenant_id=tenant.id, scopes="vehicles:read")
    r = await client.get("/api/v1/vehicles", headers={"X-Service-Token": plaintext})
    assert r.status_code == 200


async def test_superadmin_jwt_still_accepted_on_universal_endpoint(client, superadmin):
    # Regression: 2.3a's superadmin-only path is preserved.
    r = await client.get("/api/v1/passengers", headers=auth_headers(superadmin))
    assert r.status_code == 200


async def test_no_credentials_returns_401(client):
    r = await client.get("/api/v1/passengers")
    assert r.status_code == 401
