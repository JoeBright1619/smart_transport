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
│   │                               # require_role()
│   │
│   ├── models/                     # SQLAlchemy ORM models — one file per entity
│   │   ├── tenant.py               # Tenant/company account
│   │   ├── user.py
│   │   ├── vehicle.py
│   │   ├── route.py
│   │   ├── stop.py
│   │   ├── trip.py
│   │   ├── driver.py
│   │   ├── maintenance.py
│   │   ├── alert.py
│   │   ├── audit_log.py
│   │   ├── passenger_profile.py
│   │   ├── boarding_record.py
│   │   ├── refresh_token.py
│   │   └── telemetry.py
│   │
│   ├── schemas/                    # Pydantic v2 schemas — one file per entity
│   │   ├── common.py               # PaginatedResponse[T], ErrorResponse, ErrorDetail
│   │   ├── base.py                 # Base schemas and validators
│   │   ├── validators.py           # Custom validators (coordinates, phone, etc.)
│   │   ├── tenant.py
│   │   ├── user.py
│   │   ├── vehicle.py
│   │   ├── route.py
│   │   ├── trip.py
│   │   ├── driver.py
│   │   ├── maintenance.py
│   │   ├── alert.py
│   │   ├── passenger.py
│   │   ├── boarding.py
│   │   ├── arrival.py
│   │   ├── analytics.py
│   │   ├── audit.py
│   │   ├── auth.py
│   │   └── superadmin.py
│   │
│   ├── routers/                    # FastAPI routers — one file per resource
│   │   ├── auth.py                 # POST /auth/login, /auth/refresh, /auth/logout
│   │   ├── users.py                # User management
│   │   ├── passengers.py           # Passenger registration, profiles
│   │   ├── boardings.py            # Boarding/alighting records
│   │   ├── vehicles.py             # Fleet management
│   │   ├── routes.py               # Route definitions
│   │   ├── stops.py                # Stop/Station management
│   │   ├── trips.py                # Trip scheduling and lifecycle
│   │   ├── drivers.py              # Driver management
│   │   ├── maintenance.py          # Vehicle maintenance records
│   │   ├── alerts.py               # System-generated alerts
│   │   ├── analytics.py            # Fleet KPIs and aggregations
│   │   ├── arrivals.py             # Real-time ETA estimates
│   │   ├── audit.py                # Audit log retrieval
│   │   ├── superadmin.py           # Platform-level operations
│   │   └── tracking.py             # WebSocket real-time tracking
│   │
│   ├── services/                   # Business logic — one file per domain
│   │   ├── tenant_service.py       # Create, suspend, reactivate company tenants
│   │   ├── user_service.py         # User CRUD, invitation system
│   │   ├── passenger_service.py    # Passenger management
│   │   ├── passenger_report_service.py
│   │   ├── passenger_stats_service.py
│   │   ├── boarding_service.py     # Boarding/alighting logic
│   │   ├── vehicle_service.py      # Fleet CRUD, capacity tracking
│   │   ├── route_service.py        # Route management
│   │   ├── trip_service.py         # Trip scheduling, lifecycle management
│   │   ├── trip_reconciliation.py  # Trip completion reconciliation
│   │   ├── driver_service.py       # Driver management
│   │   ├── maintenance_service.py  # Maintenance scheduling
│   │   ├── alert_service.py        # Auto-generate alerts; duplicate suppression
│   │   ├── analytics_service.py    # Fleet KPIs and aggregations
│   │   ├── arrival_service.py      # Real-time ETA calculations
│   │   ├── audit_service.py        # Write to audit_logs
│   │   ├── superadmin_service.py   # Platform-level operations
│   │   ├── fleet_assignment.py     # Automatic vehicle/driver assignment
│   │   ├── fleet_position.py       # GPS position tracking
│   │   ├── simulation_runner.py    # Vehicle/traffic simulation
│   │   ├── passenger_simulation.py # Passenger demand simulation
│   │   ├── route_simulation.py     # Route simulation
│   │   └── route_trip_records.py   # Route trip data
│   │
│   └── websocket/
│       ├── manager.py              # Tenant-scoped WebSocket connection manager
│       ├── tracking.py             # Vehicle position broadcast per tenant Redis channel
│       ├── passenger_simulation.py # Real-time passenger updates
│       └── route_trip_records.py   # Real-time route trip updates
│
└── tests/
    ├── conftest.py                 # DB fixture, test client, tenant/user factories
    ├── test_auth.py
    ├── test_users.py
    ├── test_passengers.py
    ├── test_boardings.py
    ├── test_vehicles.py
    ├── test_routes.py
    ├── test_stops.py
    ├── test_trips.py
    ├── test_drivers.py
    ├── test_maintenance.py
    ├── test_alerts.py
    ├── test_analytics.py
    ├── test_arrivals.py
    ├── test_audit.py
    ├── test_superadmin.py
    ├── test_tenant_isolation.py    # REQUIRED: cross-tenant data leak tests
    └── ... (40+ additional test files for various scenarios)
```

---

## Router Registration in main.py

All routers register in `main.py`:
```python
app.include_router(auth.router)               # no prefix
app.include_router(users.router)              # /api/v1/users
app.include_router(passengers.router)         # /api/v1/passengers
app.include_router(boardings.router)          # /api/v1/boardings
app.include_router(vehicles.router)           # /api/v1/vehicles
app.include_router(routes.router)             # /api/v1/routes
app.include_router(stops.router)              # /api/v1/stops
app.include_router(trips.router)              # /api/v1/trips
app.include_router(drivers.router)            # /api/v1/drivers
app.include_router(maintenance.router)        # /api/v1/maintenance
app.include_router(alerts.router)             # /api/v1/alerts
app.include_router(analytics.router)          # /api/v1/analytics
app.include_router(arrivals.router)           # /api/v1/arrivals
app.include_router(audit.router)              # /api/v1/audit
app.include_router(superadmin.router, prefix="/superadmin")
app.include_router(tracking.router)           # WebSocket /ws/tracking
```
