from __future__ import annotations

import asyncio
import logging
import os
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.alert import Alert
from app.models.driver import Driver
from app.models.maintenance import MaintenanceRecord
from app.models.route import Route, RouteStop, Stop
from app.models.tenant import Tenant
from app.models.user import User
from app.models.vehicle import Vehicle

logger = logging.getLogger(__name__)

_TENANT_ID = "ten-demo-001"
_SUPERADMIN_PASSWORD = os.getenv("SUPERADMIN_PASSWORD", "Admin@123456")
_SEED_PASSWORD = os.getenv("SEED_PASSWORD", "Password123!")


def _log(msg: str) -> None:
    print(f"[seed] {msg}")


async def _get_or_create(
    db: AsyncSession,
    model_class: Any,
    record_id: str,
    **kwargs: Any,
) -> tuple[Any, bool]:
    existing = await db.get(model_class, record_id)
    if existing is not None:
        return existing, False
    obj = model_class(id=record_id, **kwargs)
    db.add(obj)
    return obj, True


async def _seed_superadmin(db: AsyncSession) -> None:
    _, created = await _get_or_create(
        db,
        User,
        "user-superadmin-001",
        email="superadmin@platform.local",
        password_hash=hash_password(_SUPERADMIN_PASSWORD),
        full_name="Platform Admin",
        role="superadmin",
        tenant_id=None,
        is_deleted=False,
    )
    _log(f"superadmin {'created' if created else 'already exists'}")


async def _seed_tenant(db: AsyncSession) -> None:
    _, created = await _get_or_create(
        db,
        Tenant,
        _TENANT_ID,
        name="Kigali Express Ltd",
        contact_email="admin@kigaliexpress.rw",
        is_active=True,
    )
    _log(f"tenant {_TENANT_ID} {'created' if created else 'already exists'}")


async def _seed_users(db: AsyncSession) -> None:
    users = [
        ("user-admin-001", "Jean Claude Mugabo", "admin@kigaliexpress.rw", "admin"),
        ("user-operator-001", "Marie Umutesi", "operator@kigaliexpress.rw", "operator"),
        (
            "user-dispatcher-001",
            "Eric Nsabimana",
            "dispatcher@kigaliexpress.rw",
            "dispatcher",
        ),
        (
            "user-passenger-001",
            "Alice Uwera",
            "passenger@kigaliexpress.rw",
            "passenger",
        ),
    ]
    for uid, full_name, email, role in users:
        _, created = await _get_or_create(
            db,
            User,
            uid,
            email=email,
            password_hash=hash_password(_SEED_PASSWORD),
            full_name=full_name,
            role=role,
            tenant_id=_TENANT_ID,
            is_deleted=False,
        )
        _log(f"user {uid} {'created' if created else 'already exists'}")


async def _seed_stop(db: AsyncSession, name: str, lat: float, lng: float) -> str:
    existing = await db.scalar(
        select(Stop).where(
            Stop.tenant_id == _TENANT_ID,
            Stop.name == name,
            Stop.is_deleted.is_(False),
        )
    )
    if existing is not None:
        _log(f"stop '{name}' already exists ({existing.id})")
        return existing.id

    stop = Stop(tenant_id=_TENANT_ID, name=name, lat=lat, lng=lng, is_deleted=False)
    db.add(stop)
    await db.flush()
    _log(f"stop '{name}' created ({stop.id})")
    return stop.id


async def _seed_route_stop(
    db: AsyncSession, route_id: str, stop_id: str, stop_order: int
) -> None:
    existing = await db.get(RouteStop, (route_id, stop_id))
    if existing is not None:
        return
    db.add(RouteStop(route_id=route_id, stop_id=stop_id, stop_order=stop_order))


async def _seed_routes(db: AsyncSession) -> None:
    _, r1_created = await _get_or_create(
        db,
        Route,
        "route-001",
        tenant_id=_TENANT_ID,
        name="Nyabugogo - Kimironko",
        number="101",
        distance=12.5,
        duration=35,
        is_active=True,
        color="#3B82F6",
        is_deleted=False,
    )
    _log(f"route-001 {'created' if r1_created else 'already exists'}")

    _, r2_created = await _get_or_create(
        db,
        Route,
        "route-002",
        tenant_id=_TENANT_ID,
        name="CBD - Gisozi",
        number="202",
        distance=8.0,
        duration=25,
        is_active=True,
        color="#10B981",
        is_deleted=False,
    )
    _log(f"route-002 {'created' if r2_created else 'already exists'}")

    await db.flush()

    r1_stops = [
        ("Nyabugogo", -1.9396, 30.0585),
        ("Kacyiru", -1.9453, 30.0907),
        ("Remera", -1.9553, 30.1127),
        ("Kimironko", -1.9441, 30.1341),
    ]
    for order, (name, lat, lng) in enumerate(r1_stops, start=1):
        stop_id = await _seed_stop(db, name, lat, lng)
        await _seed_route_stop(db, "route-001", stop_id, order)

    r2_stops = [
        ("CBD (City Hall)", -1.9500, 30.0588),
        ("Muhima", -1.9520, 30.0481),
        ("Gisozi", -1.9317, 30.0521),
    ]
    for order, (name, lat, lng) in enumerate(r2_stops, start=1):
        stop_id = await _seed_stop(db, name, lat, lng)
        await _seed_route_stop(db, "route-002", stop_id, order)


async def _seed_drivers(db: AsyncSession) -> dict[str, Driver]:
    drivers_data = [
        (
            "drv-001",
            "Patrick Hakizimana",
            "DL-RW-0001",
            "+250700000001",
            "available",
            date(2027, 6, 30),
        ),
        (
            "drv-002",
            "Solange Uwimana",
            "DL-RW-0002",
            "+250700000002",
            "available",
            date(2027, 9, 15),
        ),
        (
            "drv-003",
            "Claude Niyomugabo",
            "DL-RW-0003",
            "+250700000003",
            "off-duty",
            date(2026, 12, 1),
        ),
    ]
    result: dict[str, Driver] = {}
    for drv_id, name, license_num, phone, status, cert_expiry in drivers_data:
        driver, created = await _get_or_create(
            db,
            Driver,
            drv_id,
            tenant_id=_TENANT_ID,
            name=name,
            license_number=license_num,
            phone=phone,
            rating=0.0,
            total_trips=0,
            status=status,
            vehicle_id=None,
            certification_expiry=datetime(
                cert_expiry.year,
                cert_expiry.month,
                cert_expiry.day,
                tzinfo=timezone.utc,
            ),
            is_deleted=False,
        )
        result[drv_id] = driver
        _log(f"driver {drv_id} {'created' if created else 'already exists'}")
    return result


async def _seed_vehicles(
    db: AsyncSession, drivers: dict[str, Driver]
) -> dict[str, Vehicle]:
    vehicles_data = [
        (
            "veh-001",
            "RAD 001 A",
            "Yutong ZK6120",
            60,
            "active",
            "route-001",
            "drv-001",
            -1.9396,
            30.0585,
            35,
            90,
            80,
        ),
        (
            "veh-002",
            "RAD 002 B",
            "King Long XMQ",
            45,
            "idle",
            None,
            None,
            None,
            None,
            None,
            None,
            100,
        ),
        (
            "veh-003",
            "RAD 003 C",
            "Yutong ZK6120",
            60,
            "active",
            "route-002",
            "drv-002",
            -1.9500,
            30.0588,
            28,
            0,
            62,
        ),
        (
            "veh-004",
            "RAD 004 D",
            "Higer KLQ",
            30,
            "maintenance",
            None,
            None,
            None,
            None,
            None,
            None,
            100,
        ),
    ]
    result: dict[str, Vehicle] = {}
    for (
        veh_id,
        reg,
        model,
        cap,
        status,
        route_id,
        drv_id,
        lat,
        lng,
        speed,
        heading,
        fuel,
    ) in vehicles_data:
        vehicle, created = await _get_or_create(
            db,
            Vehicle,
            veh_id,
            tenant_id=_TENANT_ID,
            registration_number=reg,
            model=model,
            capacity=cap,
            status=status,
            route_id=route_id,
            driver_id=drv_id,
            lat=lat,
            lng=lng,
            speed=speed,
            heading=heading,
            fuel=fuel,
            engine_status="good",
            is_deleted=False,
        )
        result[veh_id] = vehicle
        _log(f"vehicle {veh_id} {'created' if created else 'already exists'}")
    return result


async def _link_drivers_to_vehicles(
    db: AsyncSession,
    drivers: dict[str, Driver],
    vehicles: dict[str, Vehicle],
) -> None:
    links = [("drv-001", "veh-001"), ("drv-002", "veh-003")]
    for drv_id, veh_id in links:
        driver = drivers[drv_id]
        if driver.vehicle_id != veh_id:
            driver.vehicle_id = veh_id
            _log(f"linked driver {drv_id} → vehicle {veh_id}")
        else:
            _log(f"driver {drv_id} already linked to vehicle {veh_id}")


async def _seed_maintenance(db: AsyncSession) -> None:
    records = [
        (
            "veh-004",
            "repair",
            "Engine oil leak repair",
            "in-progress",
            date(2026, 4, 5),
        ),
        (
            "veh-001",
            "routine",
            "Tyre rotation and inspection",
            "scheduled",
            date(2026, 4, 20),
        ),
    ]
    for veh_id, mtype, desc, status, sched_date in records:
        existing = await db.scalar(
            select(MaintenanceRecord).where(
                MaintenanceRecord.vehicle_id == veh_id,
                MaintenanceRecord.description == desc,
                MaintenanceRecord.is_deleted.is_(False),
            )
        )
        if existing is None:
            db.add(
                MaintenanceRecord(
                    tenant_id=_TENANT_ID,
                    vehicle_id=veh_id,
                    type=mtype,
                    description=desc,
                    scheduled_date=sched_date,
                    cost=0.0,
                    status=status,
                    is_deleted=False,
                )
            )
            _log(f"maintenance record for {veh_id} ('{desc}') created")
        else:
            _log(f"maintenance record for {veh_id} ('{desc}') already exists")


async def _seed_alerts(db: AsyncSession) -> None:
    alerts = [
        (
            "maintenance",
            "medium",
            "veh-004",
            "Maintenance Due: RAD 004 D",
            "Vehicle RAD 004 D has a maintenance record in progress.",
            False,
        ),
        (
            "speeding",
            "high",
            "veh-001",
            "Speeding Detected: RAD 001 A",
            "Vehicle RAD 001 A was detected exceeding the speed limit.",
            False,
        ),
        (
            "delay",
            "low",
            "veh-003",
            "Trip Delay: RAD 003 C",
            "Vehicle RAD 003 C is running behind schedule.",
            True,
        ),
    ]
    for atype, severity, veh_id, title, message, is_ack in alerts:
        existing = await db.scalar(
            select(Alert).where(
                Alert.tenant_id == _TENANT_ID,
                Alert.type == atype,
                Alert.vehicle_id == veh_id,
            )
        )
        if existing is None:
            db.add(
                Alert(
                    tenant_id=_TENANT_ID,
                    type=atype,
                    severity=severity,
                    title=title,
                    message=message,
                    vehicle_id=veh_id,
                    is_acknowledged=is_ack,
                )
            )
            _log(f"alert '{title}' created")
        else:
            _log(f"alert for {veh_id} ({atype}) already exists")


async def seed() -> None:
    _log("Starting seed...")
    async with AsyncSessionLocal() as db:
        await _seed_superadmin(db)
        await _seed_tenant(db)
        await _seed_users(db)
        await db.flush()

        await _seed_routes(db)
        await db.flush()

        drivers = await _seed_drivers(db)
        await db.flush()

        vehicles = await _seed_vehicles(db, drivers)
        await db.flush()

        await _link_drivers_to_vehicles(db, drivers, vehicles)
        await db.flush()

        await _seed_maintenance(db)
        await _seed_alerts(db)

        await db.commit()
    _log("Seed complete.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    asyncio.run(seed())
