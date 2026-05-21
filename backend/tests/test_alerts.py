"""Tests for alerts endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
import pytest

from app.models.alert import Alert
from app.models.trip import Trip
from app.services import alert_service
from tests.conftest import auth_headers


@pytest.fixture
async def tenant(make_tenant):
    return await make_tenant()


@pytest.fixture
async def admin(make_user, tenant):
    return await make_user(tenant_id=tenant.id, role="admin")


@pytest.fixture
async def dispatcher(make_user, tenant):
    return await make_user(tenant_id=tenant.id, role="dispatcher")


@pytest.fixture
async def passenger(make_user, tenant):
    return await make_user(tenant_id=tenant.id, role="passenger")


@pytest.fixture
async def vehicle(make_vehicle, tenant):
    return await make_vehicle(tenant_id=tenant.id)


@pytest.fixture
async def alert(db, tenant, vehicle):
    a = Alert(
        tenant_id=tenant.id,
        type="speeding",
        severity="high",
        title="Speeding Alert",
        message="Vehicle exceeding speed limit.",
        vehicle_id=vehicle.id,
        is_acknowledged=False,
    )
    db.add(a)
    await db.commit()
    return a


# ---------------------------------------------------------------------------
# GET /alerts
# ---------------------------------------------------------------------------


async def test_list_returns_200_and_includes_alert(client, admin, alert):
    r = await client.get("/api/v1/alerts", headers=auth_headers(admin))
    assert r.status_code == 200
    ids = [a["id"] for a in r.json()["data"]]
    assert alert.id in ids


async def test_list_returns_401_without_token(client):
    r = await client.get("/api/v1/alerts")
    assert r.status_code == 401


async def test_list_returns_403_for_passenger(client, passenger):
    r = await client.get("/api/v1/alerts", headers=auth_headers(passenger))
    assert r.status_code == 403


async def test_list_filter_by_severity(client, admin, alert):
    r = await client.get("/api/v1/alerts?severity=high", headers=auth_headers(admin))
    assert r.status_code == 200
    assert all(a["severity"] == "high" for a in r.json()["data"])


# ---------------------------------------------------------------------------
# POST /alerts/{id}/acknowledge
# ---------------------------------------------------------------------------


async def test_acknowledge_happy_path(client, admin, alert):
    r = await client.post(
        f"/api/v1/alerts/{alert.id}/acknowledge", headers=auth_headers(admin)
    )
    assert r.status_code == 200
    assert r.json()["data"]["isAcknowledged"] is True


async def test_acknowledge_returns_401_without_token(client, alert):
    r = await client.post(f"/api/v1/alerts/{alert.id}/acknowledge")
    assert r.status_code == 401


async def test_acknowledge_returns_404_unknown(client, admin):
    r = await client.post(
        "/api/v1/alerts/alert-does-not-exist/acknowledge",
        headers=auth_headers(admin),
    )
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Unit tests for alert_service
# ---------------------------------------------------------------------------


async def test_auto_generate_delay(db, tenant, vehicle, make_driver):
    driver = await make_driver(tenant_id=tenant.id)
    # Case 1: no active trip
    alert = await alert_service.auto_generate(db, tenant.id, "delay", vehicle.id)
    assert alert is None

    # Case 2: active trip but delay <= 5
    trip1 = Trip(
        id="trip-1",
        tenant_id=tenant.id,
        vehicle_id=vehicle.id,
        route_id="route-1",
        driver_id=driver.id,
        scheduled_start=datetime.now(timezone.utc),
        scheduled_end=datetime.now(timezone.utc),
        status="active",
        passengers=10,
        delay=3,
        is_deleted=False,
    )
    db.add(trip1)
    await db.commit()

    alert = await alert_service.auto_generate(db, tenant.id, "delay", vehicle.id)
    assert alert is None

    # Case 3: active trip with delay > 5
    trip1.delay = 10
    await db.commit()
    alert = await alert_service.auto_generate(db, tenant.id, "delay", vehicle.id)
    assert alert is not None
    assert alert.type == "delay"
    assert alert.severity == "medium"
    assert "10 minutes" in alert.message

    # Case 4: duplicate suppression (same type + vehicle + unacknowledged)
    alert2 = await alert_service.auto_generate(db, tenant.id, "delay", vehicle.id)
    assert alert2 is None


async def test_auto_generate_breakdown(db, tenant, vehicle):
    # Case 1: engine status not critical
    vehicle.engine_status = "good"
    await db.commit()
    alert = await alert_service.auto_generate(db, tenant.id, "breakdown", vehicle.id)
    assert alert is None

    # Case 2: engine status critical
    vehicle.engine_status = "critical"
    await db.commit()
    alert = await alert_service.auto_generate(db, tenant.id, "breakdown", vehicle.id)
    assert alert is not None
    assert alert.type == "breakdown"
    assert alert.severity == "critical"


async def test_auto_generate_speeding(db, tenant, vehicle):
    # Case 1: speed <= 80
    vehicle.speed = 75
    await db.commit()
    alert = await alert_service.auto_generate(db, tenant.id, "speeding", vehicle.id)
    assert alert is None

    # Case 2: speed > 80
    vehicle.speed = 85
    await db.commit()
    alert = await alert_service.auto_generate(db, tenant.id, "speeding", vehicle.id)
    assert alert is not None
    assert alert.type == "speeding"
    assert alert.severity == "high"


async def test_auto_generate_geofence(db, tenant, vehicle):
    alert = await alert_service.auto_generate(db, tenant.id, "geofence", vehicle.id)
    assert alert is not None
    assert alert.type == "geofence"
    assert alert.severity == "medium"


async def test_auto_generate_info(db, tenant, vehicle):
    alert = await alert_service.auto_generate(db, tenant.id, "info", vehicle.id)
    assert alert is not None
    assert alert.type == "info"
    assert alert.severity == "low"


async def test_auto_generate_maintenance(db, tenant, vehicle):
    alert = await alert_service.auto_generate(db, tenant.id, "maintenance", vehicle.id)
    assert alert is not None
    assert alert.type == "maintenance"
    assert alert.severity == "high"


async def test_auto_generate_unknown_type(db, tenant, vehicle):
    alert = await alert_service.auto_generate(db, tenant.id, "unknown", vehicle.id)
    assert alert is None
    alert_no_veh = await alert_service.auto_generate(db, tenant.id, "delay", None)
    assert alert_no_veh is None


async def test_get_alerts_filtering_logic(db, tenant):
    # Clear existing alerts
    await db.execute(Alert.__table__.delete())

    a1 = Alert(
        id="a1",
        tenant_id=tenant.id,
        type="speeding",
        severity="high",
        title="T1",
        message="M1",
        is_acknowledged=False,
    )
    a2 = Alert(
        id="a2",
        tenant_id=tenant.id,
        type="delay",
        severity="medium",
        title="T2",
        message="M2",
        is_acknowledged=True,
    )
    db.add_all([a1, a2])
    await db.commit()

    # Filter by severity
    res, total = await alert_service.get_alerts(db, tenant.id, severity="high")
    assert total == 1
    assert res[0].id == "a1"

    # Filter by type
    res, total = await alert_service.get_alerts(db, tenant.id, type_filter="delay")
    assert total == 1
    assert res[0].id == "a2"

    # Filter by acknowledged
    res, total = await alert_service.get_alerts(db, tenant.id, is_acknowledged=False)
    assert total == 1
    assert res[0].id == "a1"
