"""Reconcile orphaned trips.

Two producers write the ``trips`` table: the dispatch flow (clean lifecycle) and the
background simulation (fires ``start_trip``/``complete_trip`` per route loop, keyed off
volatile in-memory state). When a vehicle is deactivated/unassigned or the process
restarts mid-loop, a trip row can be left ``active``/``scheduled`` forever — which then
blocks its driver from ever going off-duty.

This module cancels such orphans and frees any driver left stuck ``on-trip``, so the
trip table self-heals. A trip is only kept if the vehicle's *current* state still backs
it (running the same driver + route).
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.driver import Driver
from app.models.trip import Trip
from app.models.vehicle import Vehicle


def _trip_is_live(trip: Trip, vehicle: Vehicle | None) -> bool:
    """True only if the vehicle's current state still backs this trip."""
    if vehicle is None or vehicle.is_deleted:
        return False
    linked = vehicle.driver_id == trip.driver_id and vehicle.route_id == trip.route_id
    if trip.status == "active":
        # An active trip must have an actively-running, still-linked vehicle.
        return vehicle.status == "active" and linked
    # scheduled: legitimate while the vehicle still reserves this driver + route and is
    # in a dispatchable state (idle, or already active for it).
    return vehicle.status in ("idle", "active") and linked


async def _has_live_trip(db: AsyncSession, driver_id: str) -> bool:
    trips = (
        await db.scalars(
            select(Trip).where(
                Trip.driver_id == driver_id,
                Trip.status.in_(["scheduled", "active"]),
                Trip.is_deleted.is_(False),
            )
        )
    ).all()
    for trip in trips:
        if _trip_is_live(trip, await db.get(Vehicle, trip.vehicle_id)):
            return True
    return False


async def reconcile_orphaned_trips(
    db: AsyncSession,
    *,
    tenant_id: str | None = None,
    driver_id: str | None = None,
) -> int:
    """Cancel active/scheduled trips no longer backed by their vehicle, freeing stuck
    drivers. Returns the number of trips reconciled. Optionally scope to a tenant/driver.
    """
    query = select(Trip).where(
        Trip.status.in_(["scheduled", "active"]),
        Trip.is_deleted.is_(False),
    )
    if tenant_id is not None:
        query = query.where(Trip.tenant_id == tenant_id)
    if driver_id is not None:
        query = query.where(Trip.driver_id == driver_id)

    trips = (await db.scalars(query)).all()
    now = datetime.now(timezone.utc)

    reconciled = 0
    affected_driver_ids: set[str] = set()
    for trip in trips:
        vehicle = await db.get(Vehicle, trip.vehicle_id)
        if _trip_is_live(trip, vehicle):
            continue
        trip.status = "cancelled"
        trip.updated_at = now
        reconciled += 1
        affected_driver_ids.add(trip.driver_id)

    # Free a driver only if they have no remaining live trip after the cancellations.
    for did in affected_driver_ids:
        driver = await db.get(Driver, did)
        if driver is None or driver.status != "on-trip":
            continue
        if not await _has_live_trip(db, did):
            driver.status = "available"

    if reconciled:
        await db.flush()
    return reconciled
