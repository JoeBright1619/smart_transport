import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.service_token_service import issue_token


@pytest.mark.asyncio
async def test_whoami_returns_token_tenant(
    client: AsyncClient, tenant, db: AsyncSession
):
    _, plaintext = await issue_token(
        db, tenant_id=tenant.id, name="gps-sim-test", scopes="vehicles:read"
    )
    await db.flush()

    resp = await client.get(
        "/api/v1/service/whoami",
        headers={"X-Service-Token": plaintext},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["tenant_id"] == tenant.id
    assert body["data"]["tenant_name"] == tenant.name


@pytest.mark.asyncio
async def test_whoami_rejects_unknown_token(client: AsyncClient):
    resp = await client.get(
        "/api/v1/service/whoami",
        headers={"X-Service-Token": "stk_live_does_not_exist"},
    )
    assert resp.status_code == 401
