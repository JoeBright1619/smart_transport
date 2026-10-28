"""Centralised driver <-> vehicle assignment.

A driver drives one vehicle at a time and a vehicle has at most one driver. The link is
stored redundantly on both sides (``Driver.vehicle_id`` and ``Vehicle.driver_id``); this
module is the single writer that keeps them in sync.

Rules:
- Reassigning a driver (or a vehicle's driver) just **moves** the assignment — you do not
  have to unassign first. Any stale link on the old side is cleared automatically.
- The **only** hard block is an **active** vehicle (one on a journey): you cannot move a
  driver off a vehicle that is active, swap the driver on an active vehicle, or unassign
  the driver from an active vehicle. End the journey first.
"""

from __future__ import annotations
from typing import NoReturn

from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import error_codes
from app.core.errors import _raise_error
from app.models.driver import Driver
from app.models.vehicle import Vehicle


def _conflict(code: str, message: str) -> NoReturn:
    _raise_error(status.HTTP_409_CONFLICT, code, message)


async def _get_vehicle(db: AsyncSession, vehicle_id: str, tenant_id: str) -> Vehicle:
    vehicle = (
        await db.execute(
            select(Vehicle).where(
                Vehicle.id == vehicle_id,
                Vehicle.tenant_id == tenant_id,
                Vehicle.is_deleted.is_(False),
            )
        )
    ).scalar_one_or_none()
    if vehicle is None:
        _raise_error(
            status.HTTP_404_NOT_FOUND,
            error_codes.VEHICLE_NOT_FOUND,
            "Vehicle not found",
        )
    return vehicle


async def _get_driver(db: AsyncSession, driver_id: str, tenant_id: str) -> Driver:
    driver = (
        await db.execute(
            select(Driver).where(
                Driver.id == driver_id,
                Driver.tenant_id == tenant_id,
                Driver.is_deleted.is_(False),
            )
        )
    ).scalar_one_or_none()
    if driver is None:
        _raise_error(
            status.HTTP_404_NOT_FOUND,
            error_codes.DRIVER_NOT_FOUND,
            "Driver not found",
        )
    return driver


async def _assign(db: AsyncSession, driver: Driver, vehicle: Vehicle) -> None:
    """Move ``driver`` onto ``vehicle``, clearing any stale links. Blocks only when an
    active vehicle would be disturbed."""
    if driver.vehicle_id == vehicle.id and vehicle.driver_id == driver.id:
        return  # already linked

    old_vehicle = None
    if driver.vehicle_id is not None and driver.vehicle_id != vehicle.id:
        old_vehicle = await db.get(Vehicle, driver.vehicle_id)

    # Active-journey guards — checked before any mutation.
    if (
        vehicle.driver_id is not None
        and vehicle.driver_id != driver.id
        and vehicle.status == "active"
    ):
        raise _conflict(
            "VEHICLE_ON_ACTIVE_JOURNEY",
            "Vehicle is on an active journey — end the journey before changing its driver",
        )
    if old_vehicle is not None and old_vehicle.status == "active":
        raise _conflict(
            "DRIVER_ON_ACTIVE_JOURNEY",
            "Driver is on an active journey — end it before reassigning them",
        )

    # Free the target vehicle's current (idle) driver, if different.
    if vehicle.driver_id is not None and vehicle.driver_id != driver.id:
        old_driver = await db.get(Driver, vehicle.driver_id)
        if old_driver is not None:
            old_driver.vehicle_id = None

    # Detach the driver from their old (idle) vehicle.
    if old_vehicle is not None and old_vehicle.driver_id == driver.id:
        old_vehicle.driver_id = None

    # Clear any other driver rows that still drift onto this vehicle.
    drifted = (
        await db.scalars(
            select(Driver).where(
                Driver.vehicle_id == vehicle.id,
                Driver.id != driver.id,
                Driver.is_deleted.is_(False),
            )
        )
    ).all()
    for other in drifted:
        other.vehicle_id = None

    driver.vehicle_id = vehicle.id
    vehicle.driver_id = driver.id


async def _unassign_vehicle(db: AsyncSession, vehicle: Vehicle) -> None:
    if vehicle.status == "active":
        raise _conflict(
            "VEHICLE_ON_ACTIVE_JOURNEY",
            "Vehicle is on an active journey — end the journey before unassigning the driver",
        )
    if vehicle.driver_id is not None:
        driver = await db.get(Driver, vehicle.driver_id)
        if driver is not None and driver.vehicle_id == vehicle.id:
            driver.vehicle_id = None
    vehicle.driver_id = None


async def _unassign_driver(db: AsyncSession, driver: Driver) -> None:
    if driver.vehicle_id is not None:
        vehicle = await db.get(Vehicle, driver.vehicle_id)
        if vehicle is not None and vehicle.status == "active":
            raise _conflict(
                "VEHICLE_ON_ACTIVE_JOURNEY",
                "Vehicle is on an active journey — end the journey before unassigning the driver",
            )
        if vehicle is not None and vehicle.driver_id == driver.id:
            vehicle.driver_id = None
    driver.vehicle_id = None


async def set_driver_assignment(
    db: AsyncSession, *, driver: Driver, vehicle_id: str | None, tenant_id: str
) -> None:
    """Assign ``driver`` to a vehicle, or unassign when ``vehicle_id`` is None.

    Reassignment moves the driver (no manual unassign needed). Blocks only when an active
    vehicle is involved. Raises 404 if the target vehicle does not exist.
    """
    if vehicle_id is None:
        await _unassign_driver(db, driver)
        return
    if driver.vehicle_id == vehicle_id:
        return
    vehicle = await _get_vehicle(db, vehicle_id, tenant_id)
    await _assign(db, driver, vehicle)


async def set_vehicle_assignment(
    db: AsyncSession, *, vehicle: Vehicle, driver_id: str | None, tenant_id: str
) -> None:
    """Assign a driver to ``vehicle``, or unassign when ``driver_id`` is None.

    Reassignment moves/replaces the driver (no manual unassign needed). Blocks only when
    an active vehicle is involved. Raises 404 if the driver does not exist.
    """
    if driver_id is None:
        await _unassign_vehicle(db, vehicle)
        return
    if vehicle.driver_id == driver_id:
        return
    driver = await _get_driver(db, driver_id, tenant_id)
    await _assign(db, driver, vehicle)
