"""Shared pytest fixtures for all test modules."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.config import settings as _settings
from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.models.driver import Driver
from app.models.route import Route, RouteStop, Stop
from app.models.tenant import Tenant
from app.models.trip import Trip
from app.models.user import User
from app.models.vehicle import Vehicle

# Force console email backend for all tests — no real emails sent
_settings.EMAIL_BACKEND = "console"

_TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


# ---------------------------------------------------------------------------
# Engine & session
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def test_engine():
    from sqlalchemy import event

    engine = create_async_engine(
        _TEST_DB_URL,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # SQLite disables foreign-key enforcement per connection. Turn it on so
    # ON DELETE CASCADE / SET NULL semantics (used by occupancy_events →
    # boarding_passenger_events and users → boarding_passenger_events) are
    # actually enforced in tests, not silently ignored.
    def _enable_sqlite_fks(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    event.listen(engine.sync_engine, "connect", _enable_sqlite_fks)
    try:
        yield engine
    finally:
        event.remove(engine.sync_engine, "connect", _enable_sqlite_fks)
        await engine.dispose()


@pytest_asyncio.fixture
async def _tables(test_engine):
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest_asyncio.fixture
async def db(test_engine, _tables) -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(test_engine, expire_on_commit=False) as session:
        yield session


# ---------------------------------------------------------------------------
# HTTP client
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    from main import app

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as c:
        yield c
    app.dependency_overrides.pop(get_db, None)


# ---------------------------------------------------------------------------
# JWT helper
# ---------------------------------------------------------------------------


def auth_headers(user: User) -> dict[str, str]:
    """Return Authorization headers containing a valid JWT for the given user."""
    token = create_access_token(
        {"userId": user.id, "tenantId": user.tenant_id, "role": user.role}
    )
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Entity factories
# ---------------------------------------------------------------------------


@pytest.fixture
def make_tenant(db: AsyncSession):
    async def _create(
        *,
        name: str = "Test Company",
        is_active: bool = True,
    ) -> Tenant:
        tenant = Tenant(
            id=f"ten-{uuid.uuid4()}",
            name=name,
            contact_email=f"{uuid.uuid4().hex[:8]}@test.local",
            is_active=is_active,
        )
        db.add(tenant)
        await db.flush()
        return tenant

    return _create


@pytest.fixture
async def tenant(make_tenant):
    return await make_tenant()


@pytest.fixture
def make_user(db: AsyncSession):
    async def _create(
        *,
        tenant_id: str | None,
        role: str = "admin",
        email: str | None = None,
        password: str = "TestPass123!",
        status: str = "active",
    ) -> User:
        user = User(
            id=f"user-{uuid.uuid4()}",
            tenant_id=tenant_id,
            email=email or f"{uuid.uuid4().hex[:8]}@test.local",
            password_hash=hash_password(password),
            full_name="Test User",
            role=role,
            status=status,
            is_deleted=False,
        )
        db.add(user)
        await db.flush()
        return user

    return _create


@pytest.fixture
def make_vehicle(db: AsyncSession):
    async def _create(
        *,
        tenant_id: str,
        status: str = "idle",
        route_id: str | None = None,
        driver_id: str | None = None,
        lat: float | None = None,
        lng: float | None = None,
    ) -> Vehicle:
        vehicle = Vehicle(
            id=f"veh-{uuid.uuid4()}",
            tenant_id=tenant_id,
            registration_number=f"TST {uuid.uuid4().hex[:4].upper()}",
            model="Test Bus",
            status=status,
            route_id=route_id,
            driver_id=driver_id,
            lat=lat,
            lng=lng,
            engine_status="good",
            is_deleted=False,
        )
        db.add(vehicle)
        await db.flush()
        return vehicle

    return _create


@pytest.fixture
async def vehicle(make_vehicle, tenant):
    return await make_vehicle(tenant_id=tenant.id)


@pytest.fixture
def make_route(db: AsyncSession):
    async def _create(
        *,
        tenant_id: str,
        is_active: bool = True,
    ) -> Route:
        route = Route(
            id=f"route-{uuid.uuid4()}",
            tenant_id=tenant_id,
            name="Test Route",
            number=str(uuid.uuid4().int % 9000 + 1000),
            distance=10.0,
            duration=30,
            is_active=is_active,
            color="#000000",
            is_deleted=False,
        )
        db.add(route)
        await db.flush()
        return route

    return _create


@pytest.fixture
async def route(make_route, tenant):
    return await make_route(tenant_id=tenant.id)


@pytest.fixture
def make_stop(db: AsyncSession):
    async def _create(*, tenant_id, name="Test Stop", lat=-1.9536, lng=30.0606) -> Stop:
        stop = Stop(
            id=f"stop-{uuid.uuid4()}",
            tenant_id=tenant_id,
            name=name,
            lat=lat,
            lng=lng,
            is_deleted=False,
        )
        db.add(stop)
        await db.flush()  # not commit
        return stop

    return _create


@pytest.fixture
async def stop(make_stop, tenant):
    return await make_stop(tenant_id=tenant.id)


@pytest.fixture
def make_trip(db: AsyncSession):
    async def _create(
        *,
        tenant_id: str,
        vehicle_id: str,
        route_id: str,
        driver_id: str,
        status: str = "scheduled",
    ) -> Trip:
        now = datetime.now(timezone.utc)
        trip = Trip(
            id=f"trip-{uuid.uuid4()}",
            tenant_id=tenant_id,
            vehicle_id=vehicle_id,
            route_id=route_id,
            driver_id=driver_id,
            scheduled_start=now,
            scheduled_end=now,
            status=status,
            passengers=0,
            delay=0,
            is_deleted=False,
        )
        db.add(trip)
        await db.flush()
        return trip

    return _create


@pytest.fixture
def make_driver(db: AsyncSession):
    async def _create(
        *,
        tenant_id: str,
        status: str = "available",
        vehicle_id: str | None = None,
    ) -> Driver:
        driver = Driver(
            id=f"drv-{uuid.uuid4()}",
            tenant_id=tenant_id,
            name="Test Driver",
            license_number=f"DL-{uuid.uuid4().hex[:6].upper()}",
            phone="+250700000000",
            rating=0.0,
            total_trips=0,
            status=status,
            vehicle_id=vehicle_id,
            certification_expiry=datetime(2028, 1, 1, tzinfo=timezone.utc),
            is_deleted=False,
        )
        db.add(driver)
        await db.flush()
        return driver

    return _create


@pytest.fixture
def make_gps_device(db: AsyncSession):
    """Factory fixture to create GPSDevice instances for testing."""
    from app.models.gps_device import GPSDevice

    async def _create(
        *,
        tenant_id: str,
        name: str = "Test GPS Device",
        token: str | None = None,
        device_type: str = "gps_service",
        is_active: bool = True,
    ) -> GPSDevice:
        device = GPSDevice(
            id=f"gps-{uuid.uuid4()}",
            tenant_id=tenant_id,
            name=name,
            token=token or f"token-{uuid.uuid4().hex[:16]}",
            device_type=device_type,
            is_active=is_active,
        )
        db.add(device)
        await db.flush()
        return device

    return _create


@pytest.fixture
async def admin_user(make_user, tenant) -> User:
    return await make_user(tenant_id=tenant.id, role="admin")


@pytest.fixture
async def passenger_user(make_user, tenant) -> User:
    return await make_user(tenant_id=None, role="passenger")


@pytest.fixture
async def operator_user(make_user, tenant):
    return await make_user(tenant_id=tenant.id, role="operator")


@pytest.fixture
async def dispatcher_user(make_user, tenant):
    return await make_user(tenant_id=tenant.id, role="dispatcher")


@pytest.fixture
async def driver_user(make_driver, tenant):
    return await make_driver(tenant_id=tenant.id)


@pytest.fixture
async def active_vehicle_at_stop(
    db: AsyncSession, make_vehicle, make_route, tenant, stop
):
    route = await make_route(tenant_id=tenant.id)
    db.add(RouteStop(route_id=route.id, stop_id=stop.id, stop_order=1))
    await db.flush()
    vehicle = await make_vehicle(
        tenant_id=tenant.id,
        status="active",
        route_id=route.id,
        lat=-1.9396,
        lng=30.0585,
    )
    vehicle.speed = 30
    await db.flush()
    return vehicle


@pytest.fixture
async def superadmin(make_user):
    return await make_user(tenant_id=None, role="superadmin")
