from __future__ import annotations

import asyncio
import logging
import os
import random
import sys
from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import cast, Date, delete, func, select, or_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.alert import Alert
from app.models.analytics import AnalyticsRecord
from app.models.driver import Driver
from app.models.maintenance import MaintenanceRecord
from app.models.route import Route, RouteStop, Stop
from app.models.tenant import Tenant
from app.models.trip import Trip
from app.models.user import User
from app.models.vehicle import Vehicle

logger = logging.getLogger(__name__)

_TENANT_ID = "ten-demo-001"
_SUPERADMIN_PASSWORD = os.getenv("SUPERADMIN_PASSWORD", "Admin@123456")
_SEED_PASSWORD = os.getenv("SEED_PASSWORD", "Password123!")

# Fixed RNG for reproducible historical data
_RNG = random.Random(42)  # nosec B311


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


async def _cleanup_stale_data(db: AsyncSession, reset: bool = False) -> None:
    conditions = [
        Tenant.name.ilike("%kigali%"),
        Tenant.contact_email.ilike("%kigali%"),
        Tenant.id.in_(
            select(User.tenant_id).where(
                User.email.ilike("%kigali%"),
                User.tenant_id.is_not(None),
            )
        ),
    ]
    if reset:
        conditions.append(Tenant.id == _TENANT_ID)
        await db.execute(delete(User).where(User.id == "user-superadmin-001"))

    stale_tenants = await db.scalars(select(Tenant.id).where(or_(*conditions)))
    stale_ids = stale_tenants.all()
    if not stale_ids:
        return
    _log(f"Cleaning up {len(stale_ids)} stale tenants (reset={reset})...")

    for tid in stale_ids:
        await db.execute(
            delete(RouteStop).where(
                RouteStop.route_id.in_(select(Route.id).where(Route.tenant_id == tid))
            )
        )
        await db.execute(delete(Trip).where(Trip.tenant_id == tid))
        await db.execute(
            delete(MaintenanceRecord).where(MaintenanceRecord.tenant_id == tid)
        )
        await db.execute(delete(Alert).where(Alert.tenant_id == tid))
        await db.execute(
            delete(AnalyticsRecord).where(AnalyticsRecord.tenant_id == tid)
        )

        try:
            from app.models.audit_log import AuditLog

            await db.execute(delete(AuditLog).where(AuditLog.tenant_id == tid))
        except ImportError:
            pass

        try:
            from app.models.telemetry import Telemetry

            await db.execute(delete(Telemetry).where(Telemetry.tenant_id == tid))
        except ImportError:
            pass

        try:
            from app.models.refresh_token import RefreshToken

            await db.execute(
                delete(RefreshToken).where(
                    RefreshToken.user_id.in_(
                        select(User.id).where(User.tenant_id == tid)
                    )
                )
            )
        except ImportError:
            pass

        await db.execute(
            update(Driver).where(Driver.tenant_id == tid).values(vehicle_id=None)
        )
        await db.execute(
            update(Vehicle).where(Vehicle.tenant_id == tid).values(driver_id=None)
        )

        await db.execute(delete(Vehicle).where(Vehicle.tenant_id == tid))
        await db.execute(delete(Driver).where(Driver.tenant_id == tid))
        await db.execute(delete(Route).where(Route.tenant_id == tid))
        await db.execute(delete(Stop).where(Stop.tenant_id == tid))
        await db.execute(delete(User).where(User.tenant_id == tid))
        await db.execute(delete(Tenant).where(Tenant.id == tid))

    await db.flush()
    _log("Stale data cleaned.")


async def _seed_tenant(db: AsyncSession) -> None:
    _, created = await _get_or_create(
        db,
        Tenant,
        _TENANT_ID,
        name="EcoFleet Ltd",
        contact_email="admin@ecofleet.rw",
        logo_path="/tenant-logos/Ecofleet_logo.png",
        is_active=True,
    )
    _log(f"tenant {_TENANT_ID} {'created' if created else 'already exists'}")


async def _seed_users(db: AsyncSession) -> None:
    users = [
        ("user-admin-001", "Jean Claude Mugabo", "admin@ecofleet.rw", "admin"),
        ("user-operator-001", "Marie Umutesi", "operator@ecofleet.rw", "operator"),
        (
            "user-dispatcher-001",
            "Eric Nsabimana",
            "dispatcher@ecofleet.rw",
            "dispatcher",
        ),
        (
            "user-passenger-001",
            "Alice Uwera",
            "passenger@ecofleet.rw",
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


async def _seed_passengers(db: AsyncSession) -> None:
    for n in range(1, 21):
        uid = f"user-passenger-{n:02d}"
        _, created = await _get_or_create(
            db,
            User,
            uid,
            email=f"passenger_{n}@email.com",
            password_hash=hash_password(_SEED_PASSWORD),
            full_name=f"name_{n}",
            role="passenger",
            tenant_id=None,
            is_deleted=False,
        )
        _log(f"passenger {uid} {'created' if created else 'already exists'}")


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
    # ── Route 1 ────────────────────────────────────────────────────────────────
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

    _, r3_created = await _get_or_create(
        db,
        Route,
        "route-003",
        tenant_id=_TENANT_ID,
        name="Remera - Kanombe",
        number="303",
        distance=10.2,
        duration=30,
        is_active=True,
        color="#F59E0B",
        is_deleted=False,
    )
    _log(f"route-003 {'created' if r3_created else 'already exists'}")

    _, r4_created = await _get_or_create(
        db,
        Route,
        "route-004",
        tenant_id=_TENANT_ID,
        name="Kicukiro - Nyabugogo",
        number="404",
        distance=9.5,
        duration=28,
        is_active=True,
        color="#8B5CF6",
        is_deleted=False,
    )
    _log(f"route-004 {'created' if r4_created else 'already exists'}")

    _, r5_created = await _get_or_create(
        db,
        Route,
        "route-005",
        tenant_id=_TENANT_ID,
        name="Gikondo - Kimironko",
        number="505",
        distance=14.0,
        duration=40,
        is_active=True,
        color="#EF4444",
        is_deleted=False,
    )
    _log(f"route-005 {'created' if r5_created else 'already exists'}")

    await db.flush()

    # ── Stops ──────────────────────────────────────────────────────────────────
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

    r3_stops = [
        ("Remera", -1.9553, 30.1127),  # reuses existing Remera stop
        ("Masaka", -1.9721, 30.1312),
        ("Nyanza", -1.9745, 30.1389),
        ("Kanombe Airport", -1.9688, 30.1398),
    ]
    for order, (name, lat, lng) in enumerate(r3_stops, start=1):
        stop_id = await _seed_stop(db, name, lat, lng)
        await _seed_route_stop(db, "route-003", stop_id, order)

    r4_stops = [
        ("Kicukiro", -1.9742, 30.0904),
        ("Niboye", -1.9661, 30.0785),
        ("Gitega", -1.9596, 30.0631),
        ("Nyabugogo", -1.9396, 30.0585),  # reuses existing Nyabugogo stop
    ]
    for order, (name, lat, lng) in enumerate(r4_stops, start=1):
        stop_id = await _seed_stop(db, name, lat, lng)
        await _seed_route_stop(db, "route-004", stop_id, order)

    r5_stops = [
        ("Gikondo", -1.9726, 30.0642),
        ("Sonatubes", -1.9636, 30.0795),
        ("Remera", -1.9553, 30.1127),  # reuses existing Remera stop
        ("Biryogo", -1.9502, 30.1140),
        ("Kimironko", -1.9441, 30.1341),  # reuses existing Kimironko stop
    ]
    for order, (name, lat, lng) in enumerate(r5_stops, start=1):
        stop_id = await _seed_stop(db, name, lat, lng)
        await _seed_route_stop(db, "route-005", stop_id, order)


async def _seed_drivers(db: AsyncSession) -> None:
    # total_trips approximated from 90-day history (2 trips/day for active drivers)
    drivers_data = [
        # id, name, license, phone, status, total_trips, rating, cert_expiry
        (
            "drv-001",
            "Patrick Hakizimana",
            "DL-RW-0001",
            "+250700000001",
            "available",
            178,
            4.6,
            date(2027, 6, 30),
        ),
        (
            "drv-002",
            "Solange Uwimana",
            "DL-RW-0002",
            "+250700000002",
            "available",
            182,
            4.8,
            date(2027, 9, 15),
        ),
        (
            "drv-003",
            "Claude Niyomugabo",
            "DL-RW-0003",
            "+250700000003",
            "off-duty",
            0,
            3.9,
            date(2026, 12, 1),
        ),
        (
            "drv-004",
            "Josephine Mukandori",
            "DL-RW-0004",
            "+250700000004",
            "available",
            175,
            4.5,
            date(2027, 3, 20),
        ),
        (
            "drv-005",
            "Emmanuel Ntwali",
            "DL-RW-0005",
            "+250700000005",
            "available",
            180,
            4.7,
            date(2027, 7, 10),
        ),
        (
            "drv-006",
            "Diane Ingabire",
            "DL-RW-0006",
            "+250700000006",
            "available",
            176,
            4.4,
            date(2027, 11, 5),
        ),
        (
            "drv-007",
            "Jean Baptiste Rutaganda",
            "DL-RW-0007",
            "+250700000007",
            "available",
            0,
            4.0,
            date(2028, 1, 15),
        ),
        (
            "drv-008",
            "Grace Uwamahoro",
            "DL-RW-0008",
            "+250700000008",
            "off-duty",
            0,
            4.1,
            date(2027, 4, 22),
        ),
    ]
    for (
        drv_id,
        name,
        license_num,
        phone,
        status,
        total_trips,
        rating,
        cert_expiry,
    ) in drivers_data:
        _, created = await _get_or_create(
            db,
            Driver,
            drv_id,
            tenant_id=_TENANT_ID,
            name=name,
            license_number=license_num,
            phone=phone,
            rating=rating,
            total_trips=total_trips,
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
        _log(f"driver {drv_id} {'created' if created else 'already exists'}")


async def _seed_vehicles(db: AsyncSession) -> None:
    # All vehicles start idle with no GPS — live trips will activate the relevant ones.
    # veh-004 is in maintenance (broken down, not available for dispatch).
    vehicles_data = [
        # id, reg, model, seating_capacity, fuel, engine_status, status
        ("veh-001", "RAD 001 A", "Yutong ZK6120", 60, 78, "good", "idle"),
        ("veh-002", "RAD 002 B", "King Long XMQ", 45, 100, "good", "idle"),
        ("veh-003", "RAD 003 C", "Yutong ZK6120", 60, 63, "good", "idle"),
        ("veh-004", "RAD 004 D", "Higer KLQ", 30, 100, "critical", "maintenance"),
        ("veh-005", "RAD 005 E", "Yutong ZK6120", 60, 95, "good", "idle"),
        ("veh-006", "RAD 006 F", "King Long XMQ", 45, 88, "good", "idle"),
        ("veh-007", "RAD 007 G", "Higer KLQ", 40, 55, "warning", "idle"),
        ("veh-008", "RAD 008 H", "Yutong ZK6120", 60, 91, "good", "idle"),
    ]
    for veh_id, reg, model, cap, fuel, engine_status, status in vehicles_data:
        _, created = await _get_or_create(
            db,
            Vehicle,
            veh_id,
            tenant_id=_TENANT_ID,
            registration_number=reg,
            model=model,
            seating_capacity=cap,
            status=status,
            route_id=None,
            driver_id=None,
            lat=None,
            lng=None,
            speed=0,
            heading=0,
            fuel=fuel,
            engine_status=engine_status,
            is_deleted=False,
        )
        _log(f"vehicle {veh_id} {'created' if created else 'already exists'}")


async def _seed_live_trips(db: AsyncSession) -> None:
    """Create the current live trip state — active trips running on the map and
    scheduled trips waiting in the dispatch queue.

    Active trips:   veh-001/drv-001/route-101, veh-003/drv-002/route-202, veh-007/drv-005/route-404
    Scheduled trips: veh-006/drv-004/route-303 (starts in ~30 min)

    Idle + available for new dispatch: veh-002, veh-005, veh-008
    Free drivers: drv-006, drv-007
    """
    now = datetime.now(timezone.utc)

    # ── Active trips ────────────────────────────────────────────────────────────
    # (trip_id, veh_id, route_id, drv_id, started_min_ago, duration_min, lat, lng, speed, heading, fuel)
    active = [
        (
            "trip-live-001",
            "veh-001",
            "route-001",
            "drv-001",
            28,
            35,
            -1.9396,
            30.0585,
            38,
            90,
            78,
        ),
        (
            "trip-live-002",
            "veh-003",
            "route-002",
            "drv-002",
            12,
            25,
            -1.9500,
            30.0588,
            29,
            0,
            63,
        ),
        (
            "trip-live-003",
            "veh-007",
            "route-004",
            "drv-005",
            18,
            28,
            -1.9742,
            30.0904,
            26,
            45,
            55,
        ),
    ]
    for (
        trip_id,
        veh_id,
        route_id,
        drv_id,
        started_ago,
        duration,
        lat,
        lng,
        speed,
        heading,
        fuel,
    ) in active:
        existing = await db.get(Trip, trip_id)
        if existing is None:
            actual_start = now - timedelta(minutes=started_ago)
            scheduled_start = actual_start - timedelta(minutes=2)
            scheduled_end = scheduled_start + timedelta(minutes=duration)
            db.add(
                Trip(
                    id=trip_id,
                    tenant_id=_TENANT_ID,
                    vehicle_id=veh_id,
                    route_id=route_id,
                    driver_id=drv_id,
                    scheduled_start=scheduled_start,
                    actual_start=actual_start,
                    scheduled_end=scheduled_end,
                    status="active",
                    passengers=0,
                    delay=0,
                    is_deleted=False,
                )
            )
            _log(f"live active trip {trip_id} created")
        else:
            _log(f"live active trip {trip_id} already exists")

        # Set vehicle to active with GPS at first route stop
        vehicle = (
            await db.execute(select(Vehicle).where(Vehicle.id == veh_id))
        ).scalar_one_or_none()
        if vehicle:
            vehicle.status = "active"
            vehicle.route_id = route_id
            vehicle.driver_id = drv_id
            vehicle.lat = lat
            vehicle.lng = lng
            vehicle.speed = speed
            vehicle.heading = heading
            vehicle.fuel = fuel

        # Set driver to on-trip and link to vehicle
        driver = (
            await db.execute(select(Driver).where(Driver.id == drv_id))
        ).scalar_one_or_none()
        if driver:
            driver.status = "on-trip"
            driver.vehicle_id = veh_id

    # ── Scheduled trips ─────────────────────────────────────────────────────────
    # (trip_id, veh_id, route_id, drv_id, starts_in_min, duration_min)
    scheduled = [
        ("trip-live-004", "veh-006", "route-003", "drv-004", 35, 30),
    ]
    for trip_id, veh_id, route_id, drv_id, starts_in, duration in scheduled:
        existing = await db.get(Trip, trip_id)
        if existing is None:
            scheduled_start = now + timedelta(minutes=starts_in)
            scheduled_end = scheduled_start + timedelta(minutes=duration)
            db.add(
                Trip(
                    id=trip_id,
                    tenant_id=_TENANT_ID,
                    vehicle_id=veh_id,
                    route_id=route_id,
                    driver_id=drv_id,
                    scheduled_start=scheduled_start,
                    scheduled_end=scheduled_end,
                    status="scheduled",
                    passengers=0,
                    delay=0,
                    is_deleted=False,
                )
            )
            _log(f"live scheduled trip {trip_id} created")
        else:
            _log(f"live scheduled trip {trip_id} already exists")

        # Reserve resources — vehicle and driver keep idle/available status until trip starts
        vehicle = (
            await db.execute(select(Vehicle).where(Vehicle.id == veh_id))
        ).scalar_one_or_none()
        if vehicle:
            vehicle.route_id = route_id
            vehicle.driver_id = drv_id

        driver = (
            await db.execute(select(Driver).where(Driver.id == drv_id))
        ).scalar_one_or_none()
        if driver:
            driver.vehicle_id = veh_id


async def _seed_maintenance(db: AsyncSession) -> None:
    records = [
        (
            "veh-004",
            "repair",
            "Engine oil leak repair",
            "in-progress",
            date(2026, 4, 5),
            45000.0,
        ),
        (
            "veh-001",
            "routine",
            "Tyre rotation and inspection",
            "scheduled",
            date(2026, 4, 20),
            0.0,
        ),
        (
            "veh-002",
            "inspection",
            "Annual roadworthiness inspection",
            "completed",
            date(2026, 3, 10),
            18000.0,
        ),
        (
            "veh-003",
            "routine",
            "Engine oil and filter change",
            "completed",
            date(2026, 3, 22),
            12500.0,
        ),
        (
            "veh-005",
            "repair",
            "Brake pad replacement - front axle",
            "completed",
            date(2026, 4, 1),
            35000.0,
        ),
        (
            "veh-006",
            "routine",
            "Air filter and coolant service",
            "scheduled",
            date(2026, 5, 15),
            0.0,
        ),
        (
            "veh-007",
            "inspection",
            "Transmission fluid check",
            "scheduled",
            date(2026, 5, 28),
            0.0,
        ),
        (
            "veh-008",
            "repair",
            "Side mirror replacement",
            "completed",
            date(2026, 4, 12),
            8500.0,
        ),
    ]
    for veh_id, mtype, desc, status, sched_date, cost in records:
        existing = await db.scalar(
            select(MaintenanceRecord).where(
                MaintenanceRecord.vehicle_id == veh_id,
                MaintenanceRecord.description == desc,
                MaintenanceRecord.is_deleted.is_(False),
            )
        )
        if existing is None:
            completed = (
                datetime(
                    sched_date.year,
                    sched_date.month,
                    sched_date.day,
                    17,
                    0,
                    tzinfo=timezone.utc,
                )
                if status == "completed"
                else None
            )
            db.add(
                MaintenanceRecord(
                    tenant_id=_TENANT_ID,
                    vehicle_id=veh_id,
                    type=mtype,
                    description=desc,
                    scheduled_date=sched_date,
                    completed_date=completed,
                    cost=cost,
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
            None,
            "Maintenance Due: RAD 004 D",
            "Vehicle RAD 004 D has a maintenance record in progress.",
            False,
        ),
        (
            "speeding",
            "high",
            "veh-001",
            "drv-001",
            "Speeding Detected: RAD 001 A",
            "Vehicle RAD 001 A was detected exceeding the speed limit on Route 101.",
            False,
        ),
        (
            "delay",
            "low",
            "veh-003",
            "drv-002",
            "Trip Delay: RAD 003 C",
            "Vehicle RAD 003 C is running behind schedule on Route 202.",
            True,
        ),
        (
            "breakdown",
            "critical",
            "veh-004",
            None,
            "Breakdown: RAD 004 D",
            "Vehicle RAD 004 D has been immobilised for engine repairs.",
            False,
        ),
        (
            "geofence",
            "medium",
            "veh-006",
            "drv-004",
            "Geofence Alert: RAD 006 F",
            "Vehicle RAD 006 F left the designated route zone.",
            True,
        ),
        (
            "speeding",
            "high",
            "veh-007",
            "drv-005",
            "Speeding Detected: RAD 007 G",
            "Vehicle RAD 007 G exceeded speed limit on Kicukiro - Nyabugogo.",
            False,
        ),
        (
            "delay",
            "medium",
            "veh-007",
            "drv-005",
            "Trip Delay: RAD 007 G",
            "Vehicle RAD 007 G is 12 minutes behind schedule on Route 404.",
            False,
        ),
        (
            "info",
            "low",
            None,
            None,
            "System: Seed Data Loaded",
            "Historical seed data has been loaded for demo purposes.",
            True,
        ),
    ]
    for atype, severity, veh_id, drv_id, title, message, is_ack in alerts:
        existing = await db.scalar(
            select(Alert).where(
                Alert.tenant_id == _TENANT_ID,
                Alert.title == title,
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
                    driver_id=drv_id,
                    is_acknowledged=is_ack,
                )
            )
            _log(f"alert '{title}' created")
        else:
            _log(f"alert '{title}' already exists")


# ---------------------------------------------------------------------------
# Historical trips & analytics (90-day history)
# ---------------------------------------------------------------------------

# Five service assignments used to generate historical completed trips
_ASSIGNMENTS = [
    ("veh-001", "route-001", "drv-001", 35),
    ("veh-003", "route-002", "drv-002", 25),
    ("veh-006", "route-003", "drv-004", 30),
    ("veh-007", "route-004", "drv-005", 28),
    ("veh-008", "route-005", "drv-006", 40),
]

# Two departures per vehicle per day (morning + afternoon)
_DEPARTURE_HOURS: list[tuple[int, int]] = [(7, 0), (13, 30)]

# Revenue per passenger (RWF)
_FARE_RWF = 300


def _make_trip(
    day: date,
    veh_id: str,
    route_id: str,
    drv_id: str,
    duration: int,
    departure: tuple[int, int],
) -> Trip:
    hour, minute = departure
    scheduled_start = datetime(
        day.year, day.month, day.day, hour, minute, tzinfo=timezone.utc
    )
    scheduled_end = scheduled_start + timedelta(minutes=duration)

    on_time = _RNG.random() < 0.82
    delay_min = _RNG.randint(-4, 0) if on_time else _RNG.randint(5, 18)
    passengers = _RNG.randint(28, 55)

    actual_start = scheduled_start + timedelta(minutes=max(0, delay_min // 2))
    actual_end = scheduled_end + timedelta(minutes=delay_min)

    created_at = datetime(day.year, day.month, day.day, 12, 0, tzinfo=timezone.utc)

    return Trip(
        tenant_id=_TENANT_ID,
        vehicle_id=veh_id,
        route_id=route_id,
        driver_id=drv_id,
        scheduled_start=scheduled_start,
        actual_start=actual_start,
        scheduled_end=scheduled_end,
        actual_end=actual_end,
        status="completed",
        passengers=passengers,
        delay=max(0, delay_min),
        is_deleted=False,
        created_at=created_at,
        updated_at=created_at,
    )


async def _seed_historical_trips(db: AsyncSession) -> None:
    existing_count = await db.scalar(
        select(func.count(Trip.id)).where(
            Trip.tenant_id == _TENANT_ID,
            Trip.is_deleted.is_(False),
            cast(Trip.created_at, Date) < date.today(),
        )
    )
    if (existing_count or 0) >= 100:
        _log(f"historical trips already seeded ({existing_count} found), skipping")
        return

    today = date.today()
    start_day = today - timedelta(days=90)

    total = 0
    current = start_day
    while current < today:
        for veh_id, route_id, drv_id, duration in _ASSIGNMENTS:
            for departure in _DEPARTURE_HOURS:
                trip = _make_trip(
                    current, veh_id, route_id, drv_id, duration, departure
                )
                db.add(trip)
                total += 1
        current += timedelta(days=1)

    _log(
        f"seeded {total} historical trips ({start_day} -> {today - timedelta(days=1)})"
    )


async def _seed_analytics_records(db: AsyncSession) -> None:
    existing_count = await db.scalar(
        select(func.count(AnalyticsRecord.id)).where(
            AnalyticsRecord.tenant_id == _TENANT_ID,
        )
    )
    if (existing_count or 0) >= 30:
        _log(f"analytics records already seeded ({existing_count} found), skipping")
        return

    today = date.today()
    start_day = today - timedelta(days=90)

    total = 0
    current = start_day
    while current < today:
        _RNG.seed(current.toordinal())
        daily_passengers = sum(
            _RNG.randint(28, 55)
            for _ in range(len(_ASSIGNMENTS) * len(_DEPARTURE_HOURS))
        )
        revenue = daily_passengers * _FARE_RWF * _RNG.uniform(0.90, 1.10)
        fuel = sum(_RNG.uniform(22, 35) for _ in _ASSIGNMENTS)

        existing = await db.scalar(
            select(AnalyticsRecord).where(
                AnalyticsRecord.tenant_id == _TENANT_ID,
                AnalyticsRecord.date == current,
            )
        )
        if existing is None:
            db.add(
                AnalyticsRecord(
                    tenant_id=_TENANT_ID,
                    date=current,
                    total_fuel_consumption=round(fuel, 1),
                    total_revenue=round(revenue, 0),
                )
            )
            total += 1

        current += timedelta(days=1)

    _RNG.seed(42)  # restore global seed
    _log(
        f"seeded {total} analytics records ({start_day} -> {today - timedelta(days=1)})"
    )


async def seed(reset: bool = False) -> None:
    _log("Starting seed...")
    async with AsyncSessionLocal() as db:
        await _cleanup_stale_data(db, reset=reset)
        await _seed_superadmin(db)
        await _seed_tenant(db)
        await _seed_users(db)
        await _seed_passengers(db)
        await db.flush()

        await _seed_routes(db)
        await db.flush()

        await _seed_drivers(db)
        await db.flush()

        await _seed_vehicles(db)
        await db.flush()

        # Seed live trips — activates vehicles and links drivers properly
        await _seed_live_trips(db)
        await db.flush()

        await _seed_maintenance(db)
        await _seed_alerts(db)
        await db.flush()

        await _seed_historical_trips(db)
        await db.flush()

        await _seed_analytics_records(db)

        await db.commit()
    _log("Seed complete.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    reset_flag = "--reset" in sys.argv
    asyncio.run(seed(reset=reset_flag))
