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

from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.models.driver import Driver
from app.models.route import Route
from app.models.tenant import Tenant
from app.models.user import User
from app.models.vehicle import Vehicle

_TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


# ---------------------------------------------------------------------------
# Engine & session
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def test_engine():
    return create_async_engine(
        _TEST_DB_URL,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


@pytest_asyncio.fixture(scope="session")
async def _tables(test_engine):
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db(test_engine, _tables) -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.connect() as conn:
        await conn.begin()
        session = AsyncSession(
            bind=conn,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        yield session
        await session.close()
        await conn.rollback()


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
def make_user(db: AsyncSession):
    async def _create(
        *,
        tenant_id: str | None,
        role: str = "admin",
        email: str | None = None,
        password: str = "TestPass123!",
    ) -> User:
        user = User(
            id=f"user-{uuid.uuid4()}",
            tenant_id=tenant_id,
            email=email or f"{uuid.uuid4().hex[:8]}@test.local",
            password_hash=hash_password(password),
            full_name="Test User",
            role=role,
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
            capacity=40,
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
