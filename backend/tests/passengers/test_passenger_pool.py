"""Tests for GET /api/v1/passengers — the universal passenger pool.

Passengers are tenant-agnostic (they can browse vehicles across all tenants),
so this endpoint is inherently cross-tenant. Access is restricted to
superadmin; tenant admins are excluded because passengers do not belong to
their tenant.

The machine consumer (passenger_service, Task 3.4) authenticates with a
superadmin JWT in this task; a universal service-token principal will replace
that in Task 2.3b.
"""

from __future__ import annotations

from tests.conftest import auth_headers


async def test_superadmin_sees_all_passengers(client, superadmin, make_user):
    p1 = await make_user(tenant_id=None, role="passenger")
    p2 = await make_user(tenant_id=None, role="passenger")

    r = await client.get("/api/v1/passengers", headers=auth_headers(superadmin))
    assert r.status_code == 200
    body = r.json()
    ids = {p["id"] for p in body["data"]}
    assert p1.id in ids
    assert p2.id in ids
    assert body["meta"]["total"] >= 2


async def test_excludes_non_passenger_roles(client, superadmin, make_user, tenant):
    passenger = await make_user(tenant_id=None, role="passenger")
    operator_user = await make_user(tenant_id=tenant.id, role="operator")
    tenant_admin = await make_user(tenant_id=tenant.id, role="admin")

    r = await client.get("/api/v1/passengers", headers=auth_headers(superadmin))
    assert r.status_code == 200
    ids = {p["id"] for p in r.json()["data"]}
    assert passenger.id in ids
    assert operator_user.id not in ids
    assert tenant_admin.id not in ids


async def test_rejects_tenant_admin(client, admin_user):
    r = await client.get("/api/v1/passengers", headers=auth_headers(admin_user))
    assert r.status_code == 403


async def test_rejects_passenger_role(client, passenger_user):
    r = await client.get("/api/v1/passengers", headers=auth_headers(passenger_user))
    assert r.status_code == 403


async def test_pagination(client, superadmin, make_user):
    for _ in range(5):
        await make_user(tenant_id=None, role="passenger")

    r = await client.get(
        "/api/v1/passengers?page=1&page_size=2",
        headers=auth_headers(superadmin),
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body["data"]) == 2
    assert body["meta"]["total"] >= 5
    assert body["meta"]["page"] == 1
    assert body["meta"]["pageSize"] == 2
