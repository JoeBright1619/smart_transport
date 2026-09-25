"""Tests for Task 13.3 — capacity alerts and vehicle occupancy endpoint.

Covers:
  - create_capacity_alert fires when occupancy == seating_capacity (high severity)
  - create_capacity_alert fires when occupancy > seating_capacity (critical severity)
  - create_capacity_alert is suppressed when an unacknowledged capacity alert exists
  - create_capacity_alert does nothing when occupancy < seating_capacity
  - record_stop_events triggers capacity alert at full capacity
  - GET /vehicles/{id}/occupancy returns correct status and remaining_seats
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import auth_headers

_PATCH = "app.websocket.manager.manager.publish_to_tenant"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def admin(make_user, tenant):
    return await make_user(tenant_id=tenant.id, role="admin")


@pytest.fixture
async def vehicle(make_vehicle, tenant):
    return await make_vehicle(
        tenant_id=tenant.id,
        status="active",
        lat=-1.9536,
        lng=30.0606,
    )


# ---------------------------------------------------------------------------
# create_capacity_alert unit tests
# ---------------------------------------------------------------------------


async def test_capacity_alert_no_fire_below_capacity(db: AsyncSession, vehicle):
    from app.services.alert_service import create_capacity_alert

    alert = await create_capacity_alert(
        db, vehicle, vehicle.seating_capacity - 1, "Stop A"
    )
    assert alert is None


async def test_capacity_alert_high_severity_when_full(db: AsyncSession, vehicle):
    from app.services.alert_service import create_capacity_alert

    with patch(_PATCH, new_callable=AsyncMock):
        alert = await create_capacity_alert(
            db, vehicle, vehicle.seating_capacity, "Stop A"
        )

    assert alert is not None
    assert alert.type == "capacity"
    assert alert.severity == "high"
    assert vehicle.registration_number in alert.title
    assert "Stop A" in alert.message


async def test_capacity_alert_critical_when_overcapacity(db: AsyncSession, vehicle):
    from app.services.alert_service import create_capacity_alert

    with patch(_PATCH, new_callable=AsyncMock):
        alert = await create_capacity_alert(
            db, vehicle, vehicle.seating_capacity + 3, "End Stop"
        )

    assert alert is not None
    assert alert.severity == "critical"
    assert "Excess" in alert.title


async def test_capacity_alert_suppressed_when_existing(db: AsyncSession, vehicle):
    from app.services.alert_service import create_capacity_alert

    with patch(_PATCH, new_callable=AsyncMock):
        first = await create_capacity_alert(
            db, vehicle, vehicle.seating_capacity, "Stop A"
        )
        second = await create_capacity_alert(
            db, vehicle, vehicle.seating_capacity, "Stop B"
        )

    assert first is not None
    assert second is None  # suppressed — unacknowledged alert already exists


async def test_capacity_alert_broadcasts_ws_event(db: AsyncSession, vehicle):
    from app.services.alert_service import create_capacity_alert

    with patch(_PATCH, new_callable=AsyncMock) as mock_publish:
        await create_capacity_alert(db, vehicle, vehicle.seating_capacity, "Stop A")

    assert mock_publish.called
    tenant_arg, payload = mock_publish.call_args[0]
    assert tenant_arg == vehicle.tenant_id
    assert payload["type"] == "new_alert"
    assert payload["alert"]["type"] == "capacity"


# ---------------------------------------------------------------------------
# boarding_service integration: alert fires at capacity
# ---------------------------------------------------------------------------


async def test_record_stop_events_triggers_alert_at_capacity(db: AsyncSession, vehicle):
    from datetime import datetime, timezone

    from app.services.boarding_service import record_stop_events

    now = datetime.now(timezone.utc)

    with patch(_PATCH, new_callable=AsyncMock) as mock_publish:
        await record_stop_events(
            db,
            vehicle,
            "stop-001",
            boarding_count=vehicle.seating_capacity,
            alighting_count=0,
            occupancy_after_boarding=vehicle.seating_capacity,
            now=now,
            stop_name="Central Terminal",
        )

    assert mock_publish.called
    _, payload = mock_publish.call_args[0]
    assert payload["type"] == "new_alert"


async def test_record_stop_events_no_alert_below_capacity(db: AsyncSession, vehicle):
    from datetime import datetime, timezone

    from app.services.boarding_service import record_stop_events

    now = datetime.now(timezone.utc)

    with patch(_PATCH, new_callable=AsyncMock) as mock_publish:
        await record_stop_events(
            db,
            vehicle,
            "stop-001",
            boarding_count=1,
            alighting_count=0,
            occupancy_after_boarding=vehicle.seating_capacity - 5,
            now=now,
            stop_name="Market",
        )

    assert not mock_publish.called


# ---------------------------------------------------------------------------
# GET /vehicles/{id}/occupancy endpoint tests
# ---------------------------------------------------------------------------


async def test_occupancy_endpoint_available(client, admin, vehicle):
    r = await client.get(
        f"/api/v1/vehicles/{vehicle.id}/occupancy",
        headers=auth_headers(admin),
    )
    assert r.status_code == 200
    body = r.json()["data"]
    assert body["vehicleId"] == vehicle.id
    assert body["seatingCapacity"] == vehicle.seating_capacity
    assert body["currentOccupancy"] == 0
    assert body["remainingSeats"] == vehicle.seating_capacity
    assert body["status"] == "available"


async def test_occupancy_endpoint_nearly_full(client, admin, db, vehicle):
    from sqlalchemy import update as sa_update

    from app.models.vehicle import Vehicle

    await db.execute(
        sa_update(Vehicle)
        .where(Vehicle.id == vehicle.id)
        .values(current_occupancy=vehicle.seating_capacity - 5)
    )
    await db.commit()

    r = await client.get(
        f"/api/v1/vehicles/{vehicle.id}/occupancy",
        headers=auth_headers(admin),
    )
    assert r.status_code == 200
    body = r.json()["data"]
    assert body["status"] == "nearly_full"
    assert body["remainingSeats"] == 5


async def test_occupancy_endpoint_full(client, admin, db, vehicle):
    from sqlalchemy import update as sa_update

    from app.models.vehicle import Vehicle

    await db.execute(
        sa_update(Vehicle)
        .where(Vehicle.id == vehicle.id)
        .values(current_occupancy=vehicle.seating_capacity)
    )
    await db.commit()

    r = await client.get(
        f"/api/v1/vehicles/{vehicle.id}/occupancy",
        headers=auth_headers(admin),
    )
    assert r.status_code == 200
    body = r.json()["data"]
    assert body["status"] == "full"
    assert body["remainingSeats"] == 0


async def test_occupancy_endpoint_returns_404_unknown(client, admin):
    r = await client.get(
        "/api/v1/vehicles/no-such-vehicle/occupancy",
        headers=auth_headers(admin),
    )
    assert r.status_code == 404


async def test_occupancy_endpoint_requires_auth(client, vehicle):
    r = await client.get(f"/api/v1/vehicles/{vehicle.id}/occupancy")
    assert r.status_code == 401
