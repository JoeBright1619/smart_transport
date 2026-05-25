from __future__ import annotations

import asyncio
import logging
import os
import random
from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import cast, Date, func, select
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


async def _seed_tenant(db: AsyncSession) -> None:
    _, created = await _get_or_create(
        db,
        Tenant,
        _TENANT_ID,
        name="EcoFleet Ltd",
        contact_email="admin@ecofleet.rw",
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
        (
            "drv-004",
            "Josephine Mukandori",
            "DL-RW-0004",
            "+250700000004",
            "available",
            date(2027, 3, 20),
        ),
        (
            "drv-005",
            "Emmanuel Ntwali",
            "DL-RW-0005",
            "+250700000005",
            "available",
            date(2027, 7, 10),
        ),
        (
            "drv-006",
            "Diane Ingabire",
            "DL-RW-0006",
            "+250700000006",
            "available",
            date(2027, 11, 5),
        ),
        (
            "drv-007",
            "Jean Baptiste Rutaganda",
            "DL-RW-0007",
            "+250700000007",
            "available",
            date(2028, 1, 15),
        ),
        (
            "drv-008",
            "Grace Uwamahoro",
            "DL-RW-0008",
            "+250700000008",
            "off-duty",
            date(2027, 4, 22),
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


async def _seed_vehicles(db: AsyncSession) -> dict[str, Vehicle]:
    vehicles_data = [
        # id,       reg,          model,             cap, status,        route,       driver,    lat,      lng,     speed, hdg, fuel
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
        (
            "veh-005",
            "RAD 005 E",
            "Yutong ZK6120",
            60,
            "idle",
            None,
            None,
            None,
            None,
            None,
            None,
            95,
        ),
        (
            "veh-006",
            "RAD 006 F",
            "King Long XMQ",
            45,
            "active",
            "route-003",
            "drv-004",
            -1.9553,
            30.1127,
            30,
            180,
            74,
        ),
        (
            "veh-007",
            "RAD 007 G",
            "Higer KLQ",
            40,
            "active",
            "route-004",
            "drv-005",
            -1.9742,
            30.0904,
            25,
            45,
            58,
        ),
        (
            "veh-008",
            "RAD 008 H",
            "Yutong ZK6120",
            60,
            "active",
            "route-005",
            "drv-006",
            -1.9726,
            30.0642,
            32,
            270,
            67,
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


def _link_drivers_to_vehicles(drivers: dict[str, Driver]) -> None:
    links = [
        ("drv-001", "veh-001"),
        ("drv-002", "veh-003"),
        ("drv-004", "veh-006"),
        ("drv-005", "veh-007"),
        ("drv-006", "veh-008"),
    ]
    for drv_id, veh_id in links:
        driver = drivers[drv_id]
        if driver.vehicle_id != veh_id:
            driver.vehicle_id = veh_id
            _log(f"linked driver {drv_id} -> vehicle {veh_id}")
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
            "veh-008",
            "drv-006",
            "Speeding Detected: RAD 008 H",
            "Vehicle RAD 008 H exceeded speed limit on Gikondo - Kimironko.",
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

# Five active service assignments: (vehicle_id, route_id, driver_id, route_duration_min)
_ASSIGNMENTS = [
    ("veh-001", "route-001", "drv-001", 35),
    ("veh-003", "route-002", "drv-002", 25),
    ("veh-006", "route-003", "drv-004", 30),
    ("veh-007", "route-004", "drv-005", 28),
    ("veh-008", "route-005", "drv-006", 40),
]

# Two departures per vehicle per day (morning + afternoon)
_DEPARTURE_HOURS: list[tuple[int, int]] = [(7, 0), (13, 30)]

# Revenue per passenger (RWF) — realistic Kigali fare range
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

    # 82 % of trips are on time
    on_time = _RNG.random() < 0.82
    delay_min = _RNG.randint(-4, 0) if on_time else _RNG.randint(5, 18)
    passengers = _RNG.randint(28, 55)

    actual_start = scheduled_start + timedelta(minutes=max(0, delay_min // 2))
    actual_end = scheduled_end + timedelta(minutes=delay_min)

    # Use noon on the historical day as created_at so the date cast is unambiguous
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
    # Skip if substantial historical data already exists
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
    # Skip if records already exist for the past window
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

    # Average passengers per day: 5 vehicles × 2 trips × avg 41 passengers ≈ 410
    # Revenue = passengers × _FARE_RWF + some variability
    # Fuel = 5 active vehicles × ~25–35 L each

    total = 0
    current = start_day
    while current < today:
        # Passengers from trips that day (approximated deterministically)
        _RNG.seed(current.toordinal())  # day-specific seed for consistency
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

        await _seed_vehicles(db)
        await db.flush()

        _link_drivers_to_vehicles(drivers)
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
    asyncio.run(seed())
