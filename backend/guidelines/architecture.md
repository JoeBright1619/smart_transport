# Backend — Project Architecture

> The recommended folder structure for the FastAPI backend.
> Follow this structure exactly when creating new files or modules.

---

## Full Directory Layout

```
backend/
├── main.py                         # FastAPI app factory, router registration, startup events
├── .env.example                    # Env var template — no actual secrets ever committed
├── requirements.txt                # Pinned dependencies
├── alembic/                        # DB migration scripts
│   ├── env.py
│   └── versions/
│       └── <timestamp>_<description>.py
│
├── app/
│   ├── core/
│   │   ├── config.py               # pydantic-settings: loads all env vars
│   │   ├── database.py             # Async SQLAlchemy engine + session factory
│   │   ├── security.py             # JWT creation/verification, bcrypt hashing
│   │   └── dependencies.py         # get_db, get_current_user, get_current_tenant,
│   │                               # require_role(), require_feature()
│   │
│   ├── models/                     # SQLAlchemy ORM models — one file per entity
│   │   ├── tenant.py               # Tenant + Subscription
│   │   ├── user.py
│   │   ├── vehicle.py
│   │   ├── route.py
│   │   ├── trip.py
│   │   ├── driver.py
│   │   ├── maintenance.py
│   │   ├── alert.py
│   │   └── audit_log.py
│   │
│   ├── schemas/                    # Pydantic v2 schemas — one file per entity
│   │   ├── common.py               # PaginatedResponse[T], ErrorResponse, ErrorDetail
│   │   ├── tenant.py
│   │   ├── user.py
│   │   ├── vehicle.py
│   │   ├── route.py
│   │   ├── trip.py
│   │   ├── driver.py
│   │   ├── maintenance.py
│   │   └── alert.py
│   │
│   ├── routers/                    # FastAPI routers — one file per resource
│   │   ├── auth.py                 # POST /auth/login, /auth/refresh, /auth/logout
│   │   ├── users.py                # GET/POST/PATCH /api/v1/users
│   │   ├── vehicles.py
│   │   ├── routes.py
│   │   ├── trips.py
│   │   ├── drivers.py
│   │   ├── maintenance.py
│   │   ├── alerts.py
│   │   ├── analytics.py
│   │   └── superadmin.py           # /superadmin/tenants, /superadmin/users, /superadmin/analytics
│   │
│   ├── services/                   # Business logic — one file per domain
│   │   ├── tenant_service.py       # Create, suspend, reactivate tenants; vehicle limit check
│   │   ├── vehicle_service.py
│   │   ├── trip_service.py
│   │   ├── dispatch_service.py
│   │   ├── maintenance_service.py
│   │   ├── alert_service.py        # Auto-generate alerts; duplicate suppression
│   │   ├── analytics_service.py
│   │   └── audit_service.py        # Write to audit_logs; called by all mutating services
│   │
│   └── websocket/
│       ├── manager.py              # Tenant-scoped WebSocket connection manager
│       └── tracking.py             # Vehicle position broadcast per tenant Redis channel
│
└── tests/
    ├── conftest.py                 # DB fixture, test client, tenant/user factories
    ├── test_auth.py
    ├── test_vehicles.py
    ├── test_trips.py
    ├── test_drivers.py
    ├── test_alerts.py
    ├── test_analytics.py
    ├── test_superadmin.py
    └── test_tenant_isolation.py    # REQUIRED: cross-tenant data leak tests
```

---

## Router Registration in main.py

All routers register in `main.py`:
```python
app.include_router(auth_router)               # no prefix
app.include_router(users_router,        prefix="/api/v1")
app.include_router(vehicles_router,     prefix="/api/v1")
app.include_router(routes_router,       prefix="/api/v1")
app.include_router(trips_router,        prefix="/api/v1")
app.include_router(drivers_router,      prefix="/api/v1")
app.include_router(maintenance_router,  prefix="/api/v1")
app.include_router(alerts_router,       prefix="/api/v1")
app.include_router(analytics_router,    prefix="/api/v1")
app.include_router(superadmin_router,   prefix="/superadmin")  # no /api/v1
```
