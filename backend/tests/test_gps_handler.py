"""Tests for GPS position handler service."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select

from app.models.telemetry import Telemetry
from app.models.vehicle import Vehicle
from app.schemas.gps import GPSPositionUpdate
from app.services import gps_handler
from typing import Any


@pytest.fixture
async def tenant(db, make_tenant):
    return await make_tenant()


@pytest.fixture
async def vehicle(db, make_vehicle, tenant) -> Vehicle:
    return await make_vehicle(tenant_id=tenant.id, lat=0.0, lng=0.0)


@pytest.fixture
def make_gps_payload(tenant):
    """Factory fixture for building GPSPositionUpdate payloads.

    Defaults match a healthy vehicle moving normally. Pass overrides to
    customize per-test (e.g. speed=80 to trigger a speeding alert).
    """

    def _make(vehicle: Vehicle, **overrides) -> GPSPositionUpdate:
        defaults: dict[str, Any] = dict(
            vehicle_id=vehicle.id,
            tenant_id=tenant.id,
            registration_number=vehicle.registration_number,
            lat=-1.9536,
            lng=30.0606,
            speed=45,
            heading=90,
            fuel=85,
            engine_status="good",
            timestamp=datetime.now(timezone.utc),
            source="gps_service",
            device_id="gps-sim-001",
        )
        defaults.update(overrides)
        return GPSPositionUpdate(**defaults)

    return _make


# Core update tests


async def test_process_gps_update_vehicle_not_found(db, tenant):
    """Test that vehicle_not_found status is returned for unknown vehicles."""
    gps_data = GPSPositionUpdate(
        vehicle_id="veh-unknown",
        tenant_id=tenant.id,
        registration_number="UNKNOWN",
        lat=-1.9536,
        lng=30.0606,
        speed=45,
        heading=90,
        fuel=85,
        engine_status="good",
        timestamp=datetime.now(timezone.utc),
        source="gps_service",
        device_id="gps-sim-001",
    )
    result = await gps_handler.process_gps_update(db, gps_data)
    assert result["status"] == "vehicle_not_found"
    assert result["vehicle_id"] == gps_data.vehicle_id


async def test_process_gps_update_updates_vehicle_position(
    db, vehicle, make_gps_payload
):
    """Test that vehicle position, speed, and heading are updated."""
    gps_data = make_gps_payload(vehicle)
    result = await gps_handler.process_gps_update(db, gps_data)
    assert result["status"] == "processed"
    assert result["vehicle_id"] == vehicle.id

    await db.refresh(vehicle)
    assert vehicle.lat == gps_data.lat
    assert vehicle.lng == gps_data.lng
    assert vehicle.speed == gps_data.speed
    assert vehicle.heading == gps_data.heading


async def test_process_gps_update_updates_vehicle_fuel_and_engine(
    db, vehicle, make_gps_payload
):
    """Test that vehicle fuel and engine status are updated."""
    original_fuel = vehicle.fuel
    gps_data = make_gps_payload(vehicle)
    result = await gps_handler.process_gps_update(db, gps_data)
    assert result["status"] == "processed"

    await db.refresh(vehicle)
    assert vehicle.fuel == gps_data.fuel
    assert vehicle.fuel != original_fuel
    assert vehicle.engine_status == gps_data.engine_status


async def test_process_gps_update_creates_telemetry(db, vehicle, make_gps_payload):
    """Test that a telemetry record is created for each GPS update."""
    gps_data = make_gps_payload(vehicle)
    result = await gps_handler.process_gps_update(db, gps_data)
    assert result["status"] == "processed"

    result = await db.execute(
        select(Telemetry).where(
            Telemetry.vehicle_id == vehicle.id,
            Telemetry.tenant_id == gps_data.tenant_id,
        )
    )
    telemetry = result.scalars().first()

    assert telemetry is not None
    assert telemetry.lat == gps_data.lat
    assert telemetry.lng == gps_data.lng
    assert telemetry.speed == gps_data.speed
    assert telemetry.heading == gps_data.heading


async def test_process_gps_update_with_zero_speed(db, vehicle, make_gps_payload):
    """Test GPS update with zero speed (vehicle stopped)."""
    gps_data = make_gps_payload(vehicle, speed=0, heading=0, fuel=90)

    result = await gps_handler.process_gps_update(db, gps_data)
    assert result["status"] == "processed"

    await db.refresh(vehicle)
    assert vehicle.speed == 0


# Alert triggering tests


async def test_process_gps_update_triggers_low_fuel_alert(
    db, vehicle, make_gps_payload
):
    """Test that low fuel alert is triggered when fuel drops below threshold."""
    vehicle.fuel = 20
    db.add(vehicle)
    await db.commit()

    gps_data = make_gps_payload(vehicle, fuel=10)

    with patch(
        "app.services.gps_handler.auto_generate", new_callable=AsyncMock
    ) as mock_alert:
        result = await gps_handler.process_gps_update(db, gps_data)
        assert result["status"] == "processed"
        call_args = mock_alert.call_args_list
        maintenance_calls = [c for c in call_args if c[0][2] == "maintenance"]
        assert len(maintenance_calls) >= 1


async def test_process_gps_update_triggers_speeding_alert(
    db, vehicle, make_gps_payload
):
    """Test that speeding alert is triggered when speed exceeds threshold."""
    gps_data = make_gps_payload(vehicle, speed=80)

    with patch(
        "app.services.gps_handler.auto_generate", new_callable=AsyncMock
    ) as mock_alert:
        result = await gps_handler.process_gps_update(db, gps_data)
        assert result["status"] == "processed"
        call_args = mock_alert.call_args_list
        speeding_calls = [c for c in call_args if c[0][2] == "speeding"]
        assert len(speeding_calls) >= 1


async def test_process_gps_update_triggers_breakdown_alert(
    db, vehicle, make_gps_payload
):
    """Test that breakdown alert is triggered when engine status is critical."""

    gps_data = make_gps_payload(vehicle, speed=0, heading=0, engine_status="critical")

    with patch(
        "app.services.gps_handler.auto_generate", new_callable=AsyncMock
    ) as mock_alert:
        result = await gps_handler.process_gps_update(db, gps_data)
        assert result["status"] == "processed"
        breakdown_calls = [
            c for c in mock_alert.call_args_list if c[0][2] == "breakdown"
        ]
        assert len(breakdown_calls) >= 1


async def test_process_gps_update_triggers_delay_alert(db, vehicle, make_gps_payload):
    """Test that delay alert is always triggered (checked by alert service)."""

    gps_data = make_gps_payload(vehicle, fuel=90)

    with patch(
        "app.services.gps_handler.auto_generate", new_callable=AsyncMock
    ) as mock_alert:
        await gps_handler.process_gps_update(db, gps_data)
        call_args = mock_alert.call_args_list
        delay_calls = [c for c in call_args if c[0][2] == "delay"]
        assert len(delay_calls) >= 1


async def test_no_low_fuel_alert_when_already_low(db, vehicle, make_gps_payload):
    """Test that low fuel alert is not triggered when already below threshold."""
    vehicle.fuel = 10
    db.add(vehicle)
    await db.commit()

    gps_data = make_gps_payload(vehicle, fuel=5)

    with patch(
        "app.services.gps_handler.auto_generate", new_callable=AsyncMock
    ) as mock_alert:
        await gps_handler.process_gps_update(db, gps_data)
        call_args = mock_alert.call_args_list
        maintenance_calls = [c for c in call_args if c[0][2] == "maintenance"]
        assert len(maintenance_calls) == 0


async def test_process_gps_update_no_speeding_alert_when_normal(
    db, vehicle, make_gps_payload
):
    """Test normal GPS update with no speeding alert."""

    gps_data = make_gps_payload(vehicle, fuel=90)

    with patch(
        "app.services.gps_handler.auto_generate", new_callable=AsyncMock
    ) as mock_alert:
        result = await gps_handler.process_gps_update(db, gps_data)
        assert result["status"] == "processed"
        call_args = mock_alert.call_args_list
        speeding_calls = [c for c in call_args if c[0][2] == "speeding"]
        assert len(speeding_calls) == 0


async def test_process_gps_update_multiple_vehicles(
    db, make_vehicle, make_gps_payload, tenant
):
    """Test processing GPS updates for multiple vehicles."""
    vehicle1 = await make_vehicle(tenant_id=tenant.id, lat=0.0, lng=0.0)
    vehicle2 = await make_vehicle(tenant_id=tenant.id, lat=1.0, lng=1.0)

    gps_data1 = make_gps_payload(vehicle1)
    gps_data2 = make_gps_payload(
        vehicle2, lat=-1.9500, lng=30.0650, speed=55, heading=180, fuel=80
    )

    result1 = await gps_handler.process_gps_update(db, gps_data1)
    result2 = await gps_handler.process_gps_update(db, gps_data2)

    assert result1["status"] == "processed"
    assert result2["status"] == "processed"

    await db.refresh(vehicle1)
    await db.refresh(vehicle2)

    assert vehicle1.lat == gps_data1.lat
    assert vehicle2.lat == gps_data2.lat


async def test_process_gps_update_handles_deleted_vehicle(db, tenant, make_gps_payload):
    """Test that deleted vehicles are not processed."""
    import uuid

    vehicle = Vehicle(
        id=f"veh-{uuid.uuid4()}",
        tenant_id=tenant.id,
        registration_number="DEL-TEST",
        model="Test Bus",
        status="offline",
        lat=0.0,
        lng=0.0,
        is_deleted=True,
    )
    db.add(vehicle)
    await db.commit()

    gps_data = make_gps_payload(vehicle)

    result = await gps_handler.process_gps_update(db, gps_data)
    assert result["status"] == "vehicle_not_found"


async def test_process_gps_update_handles_different_tenant(
    db, make_tenant, make_vehicle, make_gps_payload
):
    """Test that vehicles from different tenants are not found."""
    tenant1 = await make_tenant(name="Tenant 1")
    tenant2 = await make_tenant(name="Tenant 2")

    vehicle = await make_vehicle(tenant_id=tenant1.id, lat=0.0, lng=0.0)

    # Build a payload claiming tenant2 but pointing at tenant1's vehicle.
    gps_data = make_gps_payload(vehicle, tenant_id=tenant2.id)

    result = await gps_handler.process_gps_update(db, gps_data)
    assert result["status"] == "vehicle_not_found"
