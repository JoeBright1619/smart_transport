"""Centralised driver <-> vehicle assignment.

A driver can drive only one vehicle at a time, and a vehicle has at most one driver.
The link is stored redundantly on both sides (``Driver.vehicle_id`` and
``Vehicle.driver_id``). This module is the single writer that keeps the two sides in
sync and rejects double-assignment, so the Fleet screen and the Drivers screen can't
drift apart or bind one driver to two vehicles.
"""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.driver import Driver
from app.models.vehicle import Vehicle


def _error_detail(code: str, message: str) -> dict:
    return {
        "data": None,
        "meta": None,
        "error": {"code": code, "message": message},
    }


_DRIVER_TAKEN = _error_detail(
    "DRIVER_ALREADY_ASSIGNED",
    "Driver is already assigned to another vehicle — unassign them first",
)
_VEHICLE_TAKEN = _error_detail(
    "VEHICLE_ALREADY_ASSIGNED",
    "Vehicle already has a different driver — unassign it first",
)


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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_error_detail("NOT_FOUND", "Vehicle not found"),
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_error_detail("NOT_FOUND", "Driver not found"),
        )
    return driver


async def _link(db: AsyncSession, driver: Driver, vehicle: Vehicle) -> None:
    """Bind driver and vehicle on both sides after verifying neither is otherwise taken."""
    if driver.vehicle_id not in (None, vehicle.id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_DRIVER_TAKEN)
    if vehicle.driver_id not in (None, driver.id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_VEHICLE_TAKEN)
    # Defensive against prior drift: another driver row may still point at this vehicle.
    other = (
        await db.execute(
            select(Driver).where(
                Driver.vehicle_id == vehicle.id,
                Driver.id != driver.id,
                Driver.is_deleted.is_(False),
            )
        )
    ).scalar_one_or_none()
    if other is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_VEHICLE_TAKEN)

    driver.vehicle_id = vehicle.id
    vehicle.driver_id = driver.id


async def _clear_driver(db: AsyncSession, driver: Driver) -> None:
    if driver.vehicle_id is not None:
        vehicle = await db.get(Vehicle, driver.vehicle_id)
        if vehicle is not None and vehicle.driver_id == driver.id:
            vehicle.driver_id = None
    driver.vehicle_id = None


async def _clear_vehicle(db: AsyncSession, vehicle: Vehicle) -> None:
    if vehicle.driver_id is not None:
        driver = await db.get(Driver, vehicle.driver_id)
        if driver is not None and driver.vehicle_id == vehicle.id:
            driver.vehicle_id = None
    vehicle.driver_id = None


async def set_driver_assignment(
    db: AsyncSession, *, driver: Driver, vehicle_id: str | None, tenant_id: str
) -> None:
    """Assign ``driver`` to a vehicle, or unassign when ``vehicle_id`` is None.

    Idempotent for an existing identical pairing. Raises 409 if the driver is already
    bound to another vehicle, or 404 if the target vehicle does not exist.
    """
    if vehicle_id is None:
        await _clear_driver(db, driver)
        return
    if driver.vehicle_id == vehicle_id:
        return
    vehicle = await _get_vehicle(db, vehicle_id, tenant_id)
    await _link(db, driver, vehicle)


async def set_vehicle_assignment(
    db: AsyncSession, *, vehicle: Vehicle, driver_id: str | None, tenant_id: str
) -> None:
    """Assign a driver to ``vehicle``, or unassign when ``driver_id`` is None.

    Idempotent for an existing identical pairing. Raises 409 if the driver is already
    bound to another vehicle, or 404 if the driver does not exist.
    """
    if driver_id is None:
        await _clear_vehicle(db, vehicle)
        return
    if vehicle.driver_id == driver_id:
        return
    driver = await _get_driver(db, driver_id, tenant_id)
    await _link(db, driver, vehicle)
