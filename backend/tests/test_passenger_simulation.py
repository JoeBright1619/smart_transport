"""Tests for passenger-linked boarding simulation (Task 4.1)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.boarding_record import BoardingRecord
from app.services.boarding_service import record_single_boarding


@pytest.fixture
async def tenant(make_tenant):
    return await make_tenant()


@pytest.fixture
async def stop(tenant, db: AsyncSession):
    from app.models.route import Stop

    s = Stop(
        id="stop-sim-test-01",
        tenant_id=tenant.id,
        name="Simulation Test Stop",
        lat=0.0,
        lng=0.0,
        is_deleted=False,
    )
    db.add(s)
    await db.commit()
    return s


@pytest.mark.asyncio
async def test_record_single_boarding_creates_linked_pair(
    db: AsyncSession, tenant, stop
):
    """Board then alight a passenger through the helper; exactly 2 linked rows exist."""
    passenger_id = "user-sim-passenger-01"
    now = datetime.now(timezone.utc)

    await record_single_boarding(
        db,
        trip_id=None,
        stop_id=stop.id,
        passenger_id=passenger_id,
        event_type="boarded",
        tenant_id=tenant.id,
        occupancy_after=5,
        now=now,
    )
    await record_single_boarding(
        db,
        trip_id=None,
        stop_id=stop.id,
        passenger_id=passenger_id,
        event_type="alighted",
        tenant_id=tenant.id,
        occupancy_after=4,
        now=now,
    )
    await db.flush()

    rows = (
        await db.scalars(
            select(BoardingRecord).where(BoardingRecord.passenger_id == passenger_id)
        )
    ).all()

    assert len(rows) == 2
    event_types = {r.event_type for r in rows}
    assert "boarded" in event_types
    assert "alighted" in event_types
    assert all(r.passenger_id == passenger_id for r in rows)
