"""Cross-tenant data isolation tests.

Verifies that a user of Tenant A cannot list, read, modify, or delete data
belonging to Tenant B. A data leak between tenants is the most severe bug.

Resources covered: vehicles, routes, drivers, trips, maintenance, alerts.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.maintenance import MaintenanceRecord
from app.models.trip import Trip
from tests.conftest import auth_headers


# ---------------------------------------------------------------------------
# Module-level setup: two independent tenants + one admin each
# ---------------------------------------------------------------------------


@pytest.fixture
async def tenant_a(make_tenant):
    return await make_tenant(name="Company A")


@pytest.fixture
async def tenant_b(make_tenant):
    return await make_tenant(name="Company B")


@pytest.fixture
async def user_a(make_user, tenant_a):
    return await make_user(tenant_id=tenant_a.id, role="admin")


# ---------------------------------------------------------------------------
# Local ORM factories (too specific for conftest)
# ---------------------------------------------------------------------------


@pytest.fixture
def make_trip(db: AsyncSession):
    async def _create(
        *, tenant_id: str, vehicle_id: str, route_id: str, driver_id: str
    ) -> Trip:
        trip = Trip(
            id=f"trip-{uuid.uuid4()}",
            tenant_id=tenant_id,
            vehicle_id=vehicle_id,
            route_id=route_id,
            driver_id=driver_id,
            scheduled_start=datetime(2026, 6, 1, 8, 0, tzinfo=timezone.utc),
            scheduled_end=datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc),
            status="scheduled",
            is_deleted=False,
        )
        db.add(trip)
        await db.flush()
        return trip

    return _create


@pytest.fixture
def make_maintenance(db: AsyncSession):
    async def _create(*, tenant_id: str, vehicle_id: str) -> MaintenanceRecord:
        record = MaintenanceRecord(
            tenant_id=tenant_id,
            vehicle_id=vehicle_id,
            type="routine",
            description="Test maintenance",
            scheduled_date=date(2026, 6, 1),
            cost=0.0,
            status="scheduled",
            is_deleted=False,
        )
        db.add(record)
        await db.flush()
        return record

    return _create


@pytest.fixture
def make_alert(db: AsyncSession):
    async def _create(*, tenant_id: str, vehicle_id: str) -> Alert:
        alert = Alert(
            tenant_id=tenant_id,
            type="info",
            severity="low",
            title="Test Alert",
            message="Test alert message",
            vehicle_id=vehicle_id,
            is_acknowledged=False,
        )
        db.add(alert)
        await db.flush()
        return alert

    return _create


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _ids(response_json: dict) -> list[str]:
    return [item["id"] for item in response_json["data"]]


# ---------------------------------------------------------------------------
# Vehicles
# ---------------------------------------------------------------------------


class TestVehicleIsolation:
    @pytest.fixture
    async def vehicle_b(self, make_vehicle, tenant_b):
        return await make_vehicle(tenant_id=tenant_b.id)

    async def test_list_hides_other_tenant(self, client, user_a, vehicle_b):
        r = await client.get("/api/v1/vehicles", headers=auth_headers(user_a))
        assert r.status_code == 200
        assert vehicle_b.id not in _ids(r.json())

    async def test_get_cross_tenant_returns_404(self, client, user_a, vehicle_b):
        r = await client.get(
            f"/api/v1/vehicles/{vehicle_b.id}", headers=auth_headers(user_a)
        )
        assert r.status_code == 404

    async def test_patch_cross_tenant_returns_404(self, client, user_a, vehicle_b):
        r = await client.patch(
            f"/api/v1/vehicles/{vehicle_b.id}",
            json={"status": "idle"},
            headers=auth_headers(user_a),
        )
        assert r.status_code == 404

    async def test_delete_cross_tenant_returns_404(self, client, user_a, vehicle_b):
        r = await client.delete(
            f"/api/v1/vehicles/{vehicle_b.id}", headers=auth_headers(user_a)
        )
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


class TestRouteIsolation:
    @pytest.fixture
    async def route_b(self, make_route, tenant_b):
        return await make_route(tenant_id=tenant_b.id)

    async def test_list_hides_other_tenant(self, client, user_a, route_b):
        r = await client.get("/api/v1/routes", headers=auth_headers(user_a))
        assert r.status_code == 200
        assert route_b.id not in _ids(r.json())

    async def test_get_cross_tenant_returns_404(self, client, user_a, route_b):
        r = await client.get(
            f"/api/v1/routes/{route_b.id}", headers=auth_headers(user_a)
        )
        assert r.status_code == 404

    async def test_patch_cross_tenant_returns_404(self, client, user_a, route_b):
        r = await client.patch(
            f"/api/v1/routes/{route_b.id}",
            json={"name": "Hijacked Route"},
            headers=auth_headers(user_a),
        )
        assert r.status_code == 404

    async def test_delete_cross_tenant_returns_404(self, client, user_a, route_b):
        r = await client.delete(
            f"/api/v1/routes/{route_b.id}", headers=auth_headers(user_a)
        )
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Drivers
# ---------------------------------------------------------------------------


class TestDriverIsolation:
    @pytest.fixture
    async def driver_b(self, make_driver, tenant_b):
        return await make_driver(tenant_id=tenant_b.id)

    async def test_list_hides_other_tenant(self, client, user_a, driver_b):
        r = await client.get("/api/v1/drivers", headers=auth_headers(user_a))
        assert r.status_code == 200
        assert driver_b.id not in _ids(r.json())

    async def test_get_cross_tenant_returns_404(self, client, user_a, driver_b):
        r = await client.get(
            f"/api/v1/drivers/{driver_b.id}", headers=auth_headers(user_a)
        )
        assert r.status_code == 404

    async def test_patch_cross_tenant_returns_404(self, client, user_a, driver_b):
        r = await client.patch(
            f"/api/v1/drivers/{driver_b.id}",
            json={"name": "Hacked Driver"},
            headers=auth_headers(user_a),
        )
        assert r.status_code == 404

    async def test_delete_cross_tenant_returns_404(self, client, user_a, driver_b):
        r = await client.delete(
            f"/api/v1/drivers/{driver_b.id}", headers=auth_headers(user_a)
        )
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Trips (no DELETE endpoint)
# ---------------------------------------------------------------------------


class TestTripIsolation:
    @pytest.fixture
    async def trip_b(self, make_trip, make_vehicle, make_route, make_driver, tenant_b):
        vehicle = await make_vehicle(tenant_id=tenant_b.id)
        route = await make_route(tenant_id=tenant_b.id)
        driver = await make_driver(tenant_id=tenant_b.id)
        return await make_trip(
            tenant_id=tenant_b.id,
            vehicle_id=vehicle.id,
            route_id=route.id,
            driver_id=driver.id,
        )

    async def test_list_hides_other_tenant(self, client, user_a, trip_b):
        r = await client.get("/api/v1/trips", headers=auth_headers(user_a))
        assert r.status_code == 200
        assert trip_b.id not in _ids(r.json())

    async def test_get_cross_tenant_returns_404(self, client, user_a, trip_b):
        r = await client.get(f"/api/v1/trips/{trip_b.id}", headers=auth_headers(user_a))
        assert r.status_code == 404

    async def test_patch_cross_tenant_returns_404(self, client, user_a, trip_b):
        r = await client.patch(
            f"/api/v1/trips/{trip_b.id}",
            json={"status": "cancelled"},
            headers=auth_headers(user_a),
        )
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Maintenance (no DELETE endpoint)
# ---------------------------------------------------------------------------


class TestMaintenanceIsolation:
    @pytest.fixture
    async def maintenance_b(self, make_maintenance, make_vehicle, tenant_b):
        vehicle = await make_vehicle(tenant_id=tenant_b.id)
        return await make_maintenance(tenant_id=tenant_b.id, vehicle_id=vehicle.id)

    async def test_list_hides_other_tenant(self, client, user_a, maintenance_b):
        r = await client.get("/api/v1/maintenance", headers=auth_headers(user_a))
        assert r.status_code == 200
        assert maintenance_b.id not in _ids(r.json())

    async def test_get_cross_tenant_returns_404(self, client, user_a, maintenance_b):
        r = await client.get(
            f"/api/v1/maintenance/{maintenance_b.id}", headers=auth_headers(user_a)
        )
        assert r.status_code == 404

    async def test_patch_cross_tenant_returns_404(self, client, user_a, maintenance_b):
        r = await client.patch(
            f"/api/v1/maintenance/{maintenance_b.id}",
            json={"status": "completed"},
            headers=auth_headers(user_a),
        )
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Alerts (only list + acknowledge available)
# ---------------------------------------------------------------------------


class TestAlertIsolation:
    @pytest.fixture
    async def alert_b(self, make_alert, make_vehicle, tenant_b):
        vehicle = await make_vehicle(tenant_id=tenant_b.id)
        return await make_alert(tenant_id=tenant_b.id, vehicle_id=vehicle.id)

    async def test_list_hides_other_tenant(self, client, user_a, alert_b):
        r = await client.get("/api/v1/alerts", headers=auth_headers(user_a))
        assert r.status_code == 200
        assert alert_b.id not in _ids(r.json())

    async def test_acknowledge_cross_tenant_returns_404(self, client, user_a, alert_b):
        r = await client.post(
            f"/api/v1/alerts/{alert_b.id}/acknowledge",
            headers=auth_headers(user_a),
        )
        assert r.status_code == 404
