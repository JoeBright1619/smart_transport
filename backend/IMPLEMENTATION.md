# Backend Implementation Plan

> **How to use this document:**
> - Work through tasks **strictly in order** — each phase depends on the previous.
> - After completing a task, tick its checkbox: `[ ]` → `[x]`
> - Keep the **Current Task Pointer** below updated after each completed task.
> - **DO NOT proceed to the next task without explicit user approval.**
> - Each task lists the guideline files to read before starting work.
> - for now ignore the provided branch, we will use `master` branch instead of the branches given in the tasks and commit messages exactly as provided.

---

## Current Task Pointer

**Next task:** Task 7.1 — WebSocket Connection Manager (`websocket/manager.py`)

After completing any task, update this pointer to the next unchecked task before stopping to report.

---

> [!IMPORTANT]
> **Agent Rule:** After completing each task, stop and report:
> 1. What was implemented
> 2. Any decisions made or problems encountered
> 3. A commit message for what was implemented
> 4. Then ask: _"Ready to proceed to the next task?"_
> Do not move forward until the user confirms.

---

## Phase 1 — Project Foundation

---

### Task 1.1 — Initialize Project Structure

**Description:**
Create the full backend folder structure as defined in the architecture guidelines. This is the skeleton — no logic yet, just the correct directories and empty `__init__.py` files to make them Python packages. Also create `requirements.txt` with all pinned dependencies and a `.env.example` file.

**Dependencies to pin in `requirements.txt`:**
- `fastapi>=0.111.0`
- `uvicorn[standard]>=0.29.0`
- `sqlalchemy>=2.0.0`
- `asyncpg>=0.29.0`
- `alembic>=1.13.0`
- `pydantic>=2.7.0`
- `pydantic-settings>=2.2.0`
- `passlib[bcrypt]>=1.7.4`
- `python-jose[cryptography]>=3.3.0`
- `redis>=5.0.0`
- `websockets>=12.0`
- `pytest>=8.0.0`
- `pytest-asyncio>=0.23.0`
- `httpx>=0.27.0`
- `ruff>=0.4.0`

**Guidelines to read first:**
- `backend/guidelines/architecture.md` — exact folder structure
- `backend/guidelines/config.md` — env var list for `.env.example`

**Branch:** `chore/init-project-structure`
**Commit:** `Initialize backend project structure and dependencies`

- [x] Task 1.1 complete

---

### Task 1.2 — Core Configuration (`core/config.py`)

**Description:**
Implement the `Settings` class using `pydantic-settings`. It must load all environment variables defined in `backend/guidelines/config.md` with correct types and defaults. Export a singleton `settings` instance to be used across the app.

**Guidelines to read first:**
- `backend/guidelines/config.md` — full env var list and types
- `backend/guidelines/patterns.md` §General — no hard-coded secrets rule

**Branch:** `chore/core-config`
**Commit:** `Add pydantic-settings configuration module`

- [x] Task 1.2 complete

---

### Task 1.3 — Database Engine (`core/database.py`)

**Description:**
Set up the async SQLAlchemy engine using `asyncpg`. Create the `AsyncSession` factory and the `get_db` dependency that yields a session and closes it after the request. Define the `Base` declarative base that all ORM models will inherit from.

**Guidelines to read first:**
- `backend/guidelines/patterns.md` — SQLAlchemy async session pattern
- `backend/guidelines/database.md` — PostgreSQL as primary DB

**Branch:** `chore/core-database`
**Commit:** `Add async SQLAlchemy engine and session factory`

- [x] Task 1.3 complete

---

### Task 1.4 — Security Utilities (`core/security.py`)

**Description:**
Implement three utilities:
1. `hash_password(password: str) -> str` — bcrypt hashing via passlib
2. `verify_password(plain: str, hashed: str) -> bool`
3. `create_access_token(data: dict) -> str` — JWT with `userId`, `tenantId`, `role` in payload
4. `decode_access_token(token: str) -> dict` — verify and decode JWT

**Guidelines to read first:**
- `backend/guidelines/patterns.md` — JWT 15-min expiry, HS256
- `shared/guidelines/auth.md` — JWT payload must contain `userId`, `tenantId`, `role`

**Branch:** `chore/core-security`
**Commit:** `Add JWT creation, verification, and bcrypt password hashing`

- [x] Task 1.4 complete

---

### Task 1.5 — Common Pydantic Schemas (`schemas/common.py`)

**Description:**
Define the shared response envelope types used by every endpoint:
- `ErrorDetail` — `{ code: str, message: str }`
- `Meta` — `{ total: int, page: int, pageSize: int }`
- `APIResponse[T]` — `{ data: T | None, meta: Meta | None, error: ErrorDetail | None }`
- `PaginatedResponse[T]` — `APIResponse` with `data: list[T]`
- `PaginationParams` — query params `page: int = 1, page_size: int = 20`

**Guidelines to read first:**
- `shared/guidelines/api-contracts.md` — standard envelope format and error envelope

**Branch:** `chore/common-schemas`
**Commit:** `Add shared API response envelope and pagination schemas`

- [x] Task 1.5 complete

---

## Phase 2 — Database Models

> Read `backend/guidelines/database.md` and `shared/guidelines/entities.md` before starting any model in this phase.
> Every model must have: `id`, `tenant_id`, `is_deleted`, `created_at`, `updated_at` (see exceptions below).

---

### Task 2.1 — Tenant/Company Model (`models/tenant.py`)

**Description:**
Create the transport company tenant ORM model:
- `Tenant` — columns: `id` (prefixed `ten-`), `name`, `contact_email`, `is_active`, `created_at`, `updated_at`. **No `tenant_id` and no `is_deleted` on this model.**

**Guidelines to read first:**
- `shared/guidelines/entities.md` — Tenant entity fields
- `backend/guidelines/database.md` — Alembic migration rules, column requirements

**Branch:** `feat/model-tenant`
**Commit:** `Add Tenant ORM model`

- [x] Task 2.1 complete

---

### Task 2.2 — User Model (`models/user.py`)

**Description:**
Create the `User` ORM model with: `id` (prefixed `user-`), `tenant_id` (FK → tenants, nullable for superadmin), `email` (unique), `password_hash`, `full_name`, `role` (enum including `superadmin`), `phone`, `is_deleted`, `created_at`, `updated_at`. Index `tenant_id`.

**Guidelines to read first:**
- `shared/guidelines/entities.md` — User entity
- `shared/guidelines/auth.md` — role enum values

**Branch:** `feat/model-user`
**Commit:** `Add User ORM model with role enum and tenant FK`

- [x] Task 2.2 complete

---

### Task 2.3 — Vehicle Model (`models/vehicle.py`)

**Description:**
Create the `Vehicle` ORM model: `id` (prefixed `veh-`), `tenant_id` (FK, indexed), `registration_number`, `model`, `capacity`, `status` (enum), `lat`, `lng`, `speed`, `heading`, `fuel`, `engine_status` (enum), `route_id` (FK nullable), `driver_id` (FK nullable), `is_deleted`, `created_at`, `updated_at`.

**Guidelines to read first:**
- `shared/guidelines/entities.md` — Vehicle entity fields and status enums
- `backend/guidelines/database.md` — required indexes

**Branch:** `feat/model-vehicle`
**Commit:** `Add Vehicle ORM model`

- [x] Task 2.3 complete

---

### Task 2.4 — Route & Stop Models (`models/route.py`)

**Description:**
Create three models:
- `Route` — `id` (prefixed `route-`), `tenant_id`, `name`, `number`, `distance`, `duration`, `is_active`, `color`, `is_deleted`, `created_at`, `updated_at`
- `Stop` — `id`, `tenant_id`, `name`, `lat`, `lng`, `is_deleted`
- `RouteStop` (junction) — `route_id` (FK), `stop_id` (FK), `stop_order`. Composite PK.

**Guidelines to read first:**
- `shared/guidelines/entities.md` — Route and Stop entities

**Branch:** `feat/model-route`
**Commit:** `Add Route, Stop, and RouteStop junction ORM models`

- [x] Task 2.4 complete

---

### Task 2.5 — Driver Model (`models/driver.py`)

**Description:**
Create `Driver`: `id` (prefixed `drv-`), `tenant_id` (FK, indexed), `name`, `license_number`, `phone`, `rating` (float), `total_trips` (int), `status` (enum), `vehicle_id` (FK nullable), `certification_expiry`, `is_deleted`, `created_at`, `updated_at`.

**Guidelines to read first:**
- `shared/guidelines/entities.md` — Driver entity

**Branch:** `feat/model-driver`
**Commit:** `Add Driver ORM model`

- [x] Task 2.5 complete

---

### Task 2.6 — Trip Model (`models/trip.py`)

**Description:**
Create `Trip`: `id` (prefixed `trip-`), `tenant_id` (FK, indexed), `vehicle_id` (FK), `route_id` (FK), `driver_id` (FK), `scheduled_start`, `actual_start` (nullable), `scheduled_end`, `actual_end` (nullable), `status` (enum), `passengers` (int), `delay` (int, minutes), `is_deleted`, `created_at`, `updated_at`.

**Guidelines to read first:**
- `shared/guidelines/entities.md` — Trip entity and status enum
- `docs/api/trips.md` — valid status transitions

**Branch:** `feat/model-trip`
**Commit:** `Add Trip ORM model`

- [x] Task 2.6 complete

---

### Task 2.7 — Maintenance Model (`models/maintenance.py`)

**Description:**
Create `MaintenanceRecord`: `id`, `tenant_id` (FK, indexed), `vehicle_id` (FK), `type` (enum), `description`, `scheduled_date`, `completed_date` (nullable), `cost` (float), `status` (enum), `next_due` (date, nullable), `is_deleted`, `created_at`, `updated_at`.

**Guidelines to read first:**
- `shared/guidelines/entities.md` — MaintenanceRecord entity

**Branch:** `feat/model-maintenance`
**Commit:** `Add MaintenanceRecord ORM model`

- [x] Task 2.7 complete

---

### Task 2.8 — Alert Model (`models/alert.py`)

**Description:**
Create `Alert`: `id`, `tenant_id` (FK, indexed), `type` (enum), `severity` (enum), `title`, `message`, `vehicle_id` (FK nullable), `driver_id` (FK nullable), `is_acknowledged` (bool, default False, indexed), `created_at`. **No `is_deleted` or `updated_at` on alerts.**

**Guidelines to read first:**
- `shared/guidelines/entities.md` — Alert entity, type and severity enums
- `backend/guidelines/patterns.md` — Alert auto-generation trigger conditions

**Branch:** `feat/model-alert`
**Commit:** `Add Alert ORM model`

- [x] Task 2.8 complete

---

### Task 2.9 — Audit Log Model (`models/audit_log.py`)

**Description:**
Create `AuditLog`: `id`, `tenant_id` (FK nullable, indexed), `user_id` (FK), `entity_type` (varchar), `entity_id` (UUID string), `action_type` (enum: `create`, `update`, `soft_delete`, `login`, `impersonate`), `metadata` (JSONB), `created_at`. **Immutable — no `is_deleted`, no `updated_at`.**

**Guidelines to read first:**
- `shared/guidelines/entities.md` — AuditLog entity
- `backend/guidelines/database.md` — audit log immutability rule

**Branch:** `feat/model-audit-log`
**Commit:** `Add AuditLog ORM model (immutable)`

- [x] Task 2.9 complete

---

### Task 2.10 — Initial Alembic Migration

**Description:**
Set up Alembic (`alembic init alembic`) and configure `env.py` to use the async engine and import all models. Generate the initial migration that creates all tables. Verify it passes `alembic upgrade head` on a clean database. Also add the required indexes from `backend/guidelines/database.md`.

**Guidelines to read first:**
- `backend/guidelines/database.md` — full list of required indexes, migration rules

**Branch:** `chore/initial-migration`
**Commit:** `Add initial Alembic migration for all tables and indexes`

- [x] Task 2.10 complete

---

### Task 2.11 — Telemetry Model (`models/telemetry.py`)

**Description:**
Create the `Telemetry` ORM model. This table is an **append-only GPS/sensor log** — one row is written per active vehicle per broadcast cycle by the tracking service.

Columns: `id` (prefixed `telem-<uuid>`), `tenant_id` (FK → tenants, indexed), `vehicle_id` (FK → vehicles, indexed), `lat` (Float), `lng` (Float), `speed` (Integer), `heading` (Integer), `timestamp` (DateTime UTC, not server_default — set explicitly at write time).

**No `is_deleted`, `updated_at`, or `created_at`** — `timestamp` is the only time column. No soft delete.

Index: composite `(tenant_id, vehicle_id, timestamp)` to support efficient range queries per vehicle.

**Guidelines to read first:**
- `shared/guidelines/entities.md` — Telemetry entity and the Telemetry section for append-only rules
- `backend/guidelines/database.md` — index requirements

**Branch:** `feat/model-telemetry`
**Commit:** `Add Telemetry ORM model (append-only GPS log)`

- [x] Task 2.11 complete

---

### Task 2.12 — Alembic Migration for Telemetry Table

**Description:**
Generate an additive Alembic migration that creates the `telemetry` table and its indexes. The initial migration (Task 2.10) predates this model, so this must be a new revision.

Run `alembic revision --autogenerate -m "add telemetry table"`, review the generated migration, and verify it runs cleanly with `alembic upgrade head` without touching any existing tables.

**Guidelines to read first:**
- `backend/guidelines/database.md` — migration rules (never modify existing migrations)

**Branch:** `chore/migration-telemetry`
**Commit:** `Add Alembic migration for telemetry table`

- [x] Task 2.12 complete

---

## Phase 3 — Dependencies & Middleware

---

### Task 3.1 — FastAPI Dependencies (`core/dependencies.py`)

**Description:**
Implement three reusable dependencies:
1. `get_current_user(token: str) -> User` — decode JWT → load User from DB
2. `get_current_tenant(user: User) -> Tenant` — load Tenant → raise `403 TENANT_INACTIVE` if `is_active = False`
3. `require_role(*roles) -> Depends` — factory that raises `403` if user role not in `roles`

**Guidelines to read first:**
- `shared/guidelines/auth.md` — role hierarchy and access rules
- `shared/guidelines/multi-tenancy.md` — tenant isolation and active-account rules
- `backend/guidelines/patterns.md` — dependency usage patterns

**Branch:** `feat/core-dependencies`
**Commit:** `Add get_current_user, get_current_tenant, and require_role dependencies`

- [x] Task 3.1 complete

---

### Task 3.2 — FastAPI App Factory (`main.py`)

**Description:**
Create `main.py` with:
- `create_app()` factory function that creates the FastAPI app
- CORS middleware configured from `settings.CORS_ORIGINS`
- Router registration for all routers (stubs — routers don't need to exist yet, just structure the registration)
- Startup event to verify DB connection
- Global exception handler that returns the standard error envelope for unhandled exceptions

**Guidelines to read first:**
- `backend/guidelines/architecture.md` — router registration pattern and prefixes
- `shared/guidelines/api-contracts.md` — standard error envelope format

**Branch:** `chore/app-factory`
**Commit:** `Add FastAPI app factory with CORS, router registration, and error handler`

- [x] Task 3.2 complete

---

## Phase 4 — Auth Implementation

---

### Task 4.1 — Auth Schemas (`schemas/auth.py` + `schemas/user.py`)

**Description:**
Define Pydantic schemas for:
- `RegisterRequest` — company + first admin fields (see `docs/api/auth.md`)
- `LoginRequest` — email, password
- `TokenResponse` — accessToken + user summary
- `UserCreate`, `UserUpdate`, `UserRead` — full CRUD schemas for users

**Guidelines to read first:**
- `docs/api/auth.md` — exact request/response shapes
- `docs/api/users.md` — user CRUD request/response shapes
- `backend/guidelines/patterns.md` — Create/Update/Read schema pattern

**Branch:** `feat/auth-schemas`
**Commit:** `Add auth and user Pydantic schemas`

- [x] Task 4.1 complete

---

### Task 4.2 — Tenant Service (`services/tenant_service.py`)

**Description:**
Implement:
- `create_tenant(db, data) -> Tenant` — creates the transport company tenant + first admin user in one transaction
- `get_tenant(db, tenant_id) -> Tenant`
- `suspend_tenant(db, tenant_id)` / `reactivate_tenant(db, tenant_id)`

**Guidelines to read first:**
- `shared/guidelines/multi-tenancy.md` — tenant isolation rules
- `backend/guidelines/patterns.md` — service layer rules, transaction wrapping

**Branch:** `feat/tenant-service`
**Commit:** `Add TenantService with create and account status management`

- [x] Task 4.2 complete

---

### Task 4.3 — Audit Service (`services/audit_service.py`)

**Description:**
Implement a single function:
- `log(db, user_id, tenant_id, entity_type, entity_id, action_type, metadata=None) -> AuditLog`

This is called by all other services after any mutation. It inserts into `audit_logs` and never modifies or deletes existing entries.

**Guidelines to read first:**
- `backend/guidelines/database.md` — audit logging requirements, immutability rule
- `shared/guidelines/entities.md` — AuditLog entity fields

**Branch:** `feat/audit-service`
**Commit:** `Add AuditService for immutable audit log writes`

- [x] Task 4.3 complete

---

### Task 4.4 — Auth Router (`routers/auth.py`)

**Description:**
Implement four endpoints:
- `POST /auth/register` — calls `tenant_service.create_tenant()`, returns tenant + user + access token; sets refresh token as HttpOnly cookie
- `POST /auth/login` — verify password, issue JWT + refresh token cookie
- `POST /auth/refresh` — read HttpOnly cookie, validate refresh token, issue new JWT + rotate refresh token
- `POST /auth/logout` — invalidate refresh token in DB/Redis

Refresh tokens must be stored in the DB (a simple `refresh_tokens` table or Redis key). Add a migration if using a DB table.

**Guidelines to read first:**
- `docs/api/auth.md` — request/response shapes for all four endpoints
- `shared/guidelines/auth.md` — JWT payload fields, HttpOnly cookie, token rotation rule

**Branch:** `feat/auth-router`
**Commit:** `Add auth router: register, login, refresh, logout`

- [x] Task 4.4 complete

---

## Phase 5 — Core Resource CRUD

> For every router in this phase, read `backend/guidelines/patterns.md` (router + service + schema rules) and the matching `docs/api/<resource>.md` file.

---

### Task 5.1 — Users CRUD

**Description:**
Implement schemas (`schemas/user.py`) if not already done, service (`services/user_service.py`), and router (`routers/users.py`) for full CRUD. All queries must filter by `tenant_id`. Soft delete + audit log on `DELETE`. Role changes must follow hierarchy rules.

**Guidelines to read first:**
- `docs/api/users.md` — endpoint shapes, role change rules
- `shared/guidelines/multi-tenancy.md` — tenant isolation rules
- `backend/guidelines/patterns.md` — service layer, schema patterns

**Branch:** `feat/users-crud`
**Commit:** `Add users service and router (CRUD with tenant isolation)`

- [x] Task 5.1 complete

---

### Task 5.2 — Vehicles CRUD

**Description:**
Implement `schemas/vehicle.py`, `services/vehicle_service.py`, and `routers/vehicles.py`. On `DELETE`, verify vehicle is not `active`. All queries scoped to `tenant_id`. Soft delete + audit log.

**Guidelines to read first:**
- `docs/api/vehicles.md` — endpoint shapes and validation rules
- `shared/guidelines/multi-tenancy.md` — tenant isolation rules
- `backend/guidelines/patterns.md`

**Branch:** `feat/vehicles-crud`
**Commit:** `Add vehicles service and router with vehicle limit enforcement`

- [x] Task 5.2 complete

---

### Task 5.3 — Routes CRUD

**Description:**
Implement `schemas/route.py`, `services/route_service.py`, and `routers/routes.py`. Creating a route must atomically create the `Route` and all `RouteStop` junction records. Updating `stops[]` replaces all existing stops. Cannot delete a route with active/scheduled trips (`409`).

**Guidelines to read first:**
- `docs/api/routes.md` — stop replacement behaviour, delete constraint

**Branch:** `feat/routes-crud`
**Commit:** `Add routes service and router with atomic stop management`

- [x] Task 5.3 complete

---

### Task 5.4 — Drivers CRUD

**Description:**
Implement `schemas/driver.py`, `services/driver_service.py`, and `routers/drivers.py`. Cannot delete a driver with `status: 'on-trip'` (`400`). All queries scoped to `tenant_id`.

**Guidelines to read first:**
- `docs/api/drivers.md`

**Branch:** `feat/drivers-crud`
**Commit:** `Add drivers service and router`

- [x] Task 5.4 complete

---

### Task 5.5 — Trips CRUD & Status Transitions

**Description:**
Implement `schemas/trip.py`, `services/trip_service.py`, and `routers/trips.py`. Status transitions: `PATCH` only changes `status`. Setting `active` must set `actual_start = now`. Setting `completed` must set `actual_end = now`. Conflict check on `POST` (vehicle or driver already has active/scheduled trip). Enforce valid transitions only.

**Guidelines to read first:**
- `docs/api/trips.md` — valid status transition table
- `backend/guidelines/patterns.md` — complex operation → single transaction

**Branch:** `feat/trips-crud`
**Commit:** `Add trips service and router with status transition enforcement`

- [x] Task 5.5 complete

---

## Phase 6 — Operations (Alerts, Maintenance, Analytics)

---

### Task 6.1 — Alert Service & Router

**Description:**
Implement `services/alert_service.py` with:
- `auto_generate(db, tenant_id, trigger_type, vehicle_id)` — checks trigger conditions from `backend/guidelines/patterns.md`, applies duplicate suppression, creates `Alert`
- `acknowledge(db, alert_id, tenant_id)` — sets `is_acknowledged = True`

Implement `routers/alerts.py` with `GET /api/v1/alerts` (filtered) and `POST /api/v1/alerts/{id}/acknowledge`.

**Guidelines to read first:**
- `backend/guidelines/patterns.md` — alert trigger conditions and duplicate suppression rules
- `docs/api/operations.md` — alert endpoint shapes

**Branch:** `feat/alerts`
**Commit:** `Add alert service with auto-generation, suppression, and acknowledge endpoint`

- [x] Task 6.1 complete

---

### Task 6.2 — Maintenance CRUD

**Description:**
Implement `schemas/maintenance.py`, `services/maintenance_service.py`, and `routers/maintenance.py`. Setting `status: "completed"` auto-fills `completed_date` if not provided.

**Guidelines to read first:**
- `docs/api/operations.md` — maintenance endpoint shapes
- `shared/guidelines/multi-tenancy.md` — tenant isolation rules

**Branch:** `feat/maintenance-crud`
**Commit:** `Add maintenance service and router`

- [x] Task 6.2 complete

---

### Task 6.3 — Analytics Router

**Description:**
Implement `services/analytics_service.py` to aggregate data from `trips`, `vehicles`, and `analytics` tables into the summary + daily breakdown format. Cache results in Redis (60-second TTL, keyed by `tenant_id + date range`). Implement `routers/analytics.py`.

**Guidelines to read first:**
- `docs/api/analytics.md` — exact response shape
- `shared/guidelines/multi-tenancy.md` — tenant isolation rules
- `backend/guidelines/patterns.md` — Redis caching rule

**Branch:** `feat/analytics`
**Commit:** `Add analytics service and router with Redis caching`

- [x] Task 6.3 complete

---

## Phase 7 — Real-Time Tracking

---

### Task 7.1 — WebSocket Connection Manager (`websocket/manager.py`)

**Description:**
Implement the `ConnectionManager` class:
- `connect(websocket, tenant_id)` — accept + store the connection keyed by `tenant_id`
- `disconnect(websocket, tenant_id)` — remove from active connections
- `broadcast_to_tenant(tenant_id, message)` — send JSON message to all connections with matching `tenant_id`
- Subscribe to `vehicle_updates:{tenant_id}` Redis channels

**Guidelines to read first:**
- `backend/guidelines/realtime.md` — tenant-scoped channel format, ConnectionManager rules
- `docs/api/tracking.md` — WebSocket message format

**Branch:** `feat/ws-connection-manager`
**Commit:** `Add tenant-scoped WebSocket ConnectionManager with Redis pub/sub`

- [ ] Task 7.1 complete

---

### Task 7.2 — Vehicle Position Broadcaster (`websocket/tracking.py`)

**Description:**
Implement the tracking endpoint `WS /ws/tracking`:
- Validate JWT from `?token=` query param; reject with code `4001` if invalid
- Register connection with `ConnectionManager` using `tenant_id` from JWT
- Implement the 5-second broadcast loop that reads current vehicle positions from DB (filtered by `tenant_id`) and publishes to `vehicle_updates:{tenant_id}` Redis channel
- **Before publishing each cycle**, write one `Telemetry` row per active vehicle with a position (skip vehicles where `lat`/`lng` is null or `status != "active"`). A write failure must log a warning but must not abort the broadcast.
- Handle clean disconnects

Also implement the GPS simulation loop for development (move seeded vehicles slightly every 5 seconds to simulate movement).

**Guidelines to read first:**
- `backend/guidelines/realtime.md` — full architecture, channel naming, broadcast rules
- `docs/api/tracking.md` — exact message format, rejection code, and Telemetry persistence contract
- `shared/guidelines/entities.md` — Telemetry entity fields and append-only rules

**Branch:** `feat/ws-tracking`
**Commit:** `Add WebSocket tracking endpoint with 5-second broadcast loop and GPS simulation`

- [ ] Task 7.2 complete

---

## Phase 8 — Arrival Time Estimation

---

### Task 8.1 — Arrivals Endpoint

**Description:**
Implement `GET /api/v1/arrivals?stopId=<id>` in `routers/arrivals.py`. The service must:
1. Load the stop by `stopId` (verify it belongs to the tenant)
2. Find all **active** vehicles whose current route serves this stop
3. For each vehicle, calculate: `distance_km = haversine(vehicle.lat, vehicle.lng, stop.lat, stop.lng)` then `eta_minutes = round((distance_km / vehicle.speed) * 60)`
4. Handle edge case: `speed == 0` → `status: "stopped"`, `etaMinutes: null`
5. Return list sorted by `etaMinutes` ascending

Implement the Haversine formula in a utility function in `app/core/geo.py`.

**Guidelines to read first:**
- `docs/api/tracking.md` — arrivals endpoint request/response shapes and edge cases
- `shared/guidelines/multi-tenancy.md` — stop ownership validation (return `404` on mismatch)

**Branch:** `feat/arrivals-eta`
**Commit:** `Add arrivals endpoint with Haversine-based ETA calculation`

- [ ] Task 8.1 complete

---

## Phase 9 — Superadmin Portal

---

### Task 9.1 — Superadmin Router

**Description:**
Implement `routers/superadmin.py` with all endpoints in `docs/api/superadmin.md`:
- `GET /superadmin/tenants` — list all tenants with vehicle + user counts
- `GET /superadmin/tenants/{id}` — full tenant detail
- `PATCH /superadmin/tenants/{id}` — suspend/reactivate tenant company accounts
- `POST /superadmin/tenants/{id}/impersonate` — return 1-hour JWT, create audit log entry
- `GET /superadmin/analytics` — platform-wide aggregated stats

All endpoints must require `role: superadmin` via `Depends(require_role("superadmin"))`.

**Guidelines to read first:**
- `docs/api/superadmin.md` — all endpoint shapes
- `shared/guidelines/auth.md` — impersonation audit log rule, superadmin JWT payload

**Branch:** `feat/superadmin-router`
**Commit:** `Add superadmin router: tenant management and impersonation`

- [ ] Task 9.1 complete

---

## Phase 10 — Seed Script & Docker

---

### Task 10.1 — Database Seed Script (`core/seed.py`)

**Description:**
Implement an idempotent seed script following `docs/Seed-Plan.md` exactly. Must create: 1 superadmin, 1 demo tenant/company, 4 demo users, 2 routes with stops, 3 drivers, 4 vehicles with initial positions, 2 maintenance records, 3 alerts. Read passwords from `SUPERADMIN_PASSWORD` and `SEED_PASSWORD` env vars. Output `[seed] ...` log lines for each step.

**Guidelines to read first:**
- `docs/Seed-Plan.md` — full seed data specification (IDs, names, coordinates, etc.)

**Branch:** `chore/seed-script`
**Commit:** `Add idempotent database seed script`

- [ ] Task 10.1 complete

---

### Task 10.2 — Docker Compose

**Description:**
Create `prototype/docker-compose.yml` with four services: `db` (postgres:15), `redis` (redis:7-alpine), `backend` (built from `backend/Dockerfile`), and optionally `frontend`. Also create `backend/Dockerfile` using a Python 3.11 slim base. The backend service must wait for DB to be healthy before starting (use `depends_on` with `healthcheck`).

**Guidelines to read first:**
- `docs/Dev-Setup.md` — Docker Compose configuration reference

**Branch:** `chore/docker-setup`
**Commit:** `Add Docker Compose and backend Dockerfile for full-stack local setup`

- [ ] Task 10.2 complete

---

## Phase 11 — Tests

---

### Task 11.1 — Test Infrastructure (`tests/conftest.py`)

**Description:**
Set up pytest fixtures:
- Async test DB session using in-memory SQLite
- `TestClient` using `httpx.AsyncClient`
- Factory fixtures: `create_tenant()`, `create_user()`, `create_vehicle()` etc.
- JWT helper: `auth_headers(role, tenant_id)` — returns `Authorization: Bearer <token>` dict

**Guidelines to read first:**
- `backend/guidelines/testing.md` — pytest-asyncio, conftest patterns, fixture structure

**Branch:** `test/conftest`
**Commit:** `Add pytest conftest with async DB, test client, and factory fixtures`

- [ ] Task 11.1 complete

---

### Task 11.2 — Tenant Isolation Tests (`tests/test_tenant_isolation.py`)

**Description:**
For every resource (`vehicles`, `routes`, `trips`, `drivers`, `maintenance`, `alerts`), verify:
1. Tenant A cannot `GET /api/v1/<resource>` and see Tenant B's data
2. Tenant A cannot `GET /api/v1/<resource>/{id}` for a Tenant B record (must return `404`)
3. Tenant A cannot `PATCH` a Tenant B record (must return `404`)
4. Tenant A cannot `DELETE` a Tenant B record (must return `404`)

This is the most important test file. All tests must pass before considering the MVP done.

**Guidelines to read first:**
- `backend/guidelines/testing.md` — tenant isolation test requirements
- `shared/guidelines/multi-tenancy.md` — isolation rules (return `404` not `403` on mismatch)

**Branch:** `test/tenant-isolation`
**Commit:** `Add cross-tenant data isolation tests for all resources`

- [ ] Task 11.2 complete

---

### Task 11.3 — Resource CRUD Tests

**Description:**
For each resource, add a test file covering: happy path, `401` (no token), `403` (wrong role), `422` (validation failure), and resource-specific edge cases (e.g., vehicle limit, status transitions, duplicate registration number).

Files: `test_auth.py`, `test_users.py`, `test_vehicles.py`, `test_routes.py`, `test_drivers.py`, `test_trips.py`, `test_alerts.py`, `test_maintenance.py`, `test_analytics.py`, `test_arrivals.py`, `test_superadmin.py`.

**Guidelines to read first:**
- `backend/guidelines/testing.md` — minimum test coverage per endpoint

**Branch:** `test/crud-coverage`
**Commit:** `Add CRUD test coverage for all resource endpoints`

- [ ] Task 11.3 complete

---

## Phase 12 — Final Polish

---

### Task 12.1 — OpenAPI Annotations

**Description:**
Add `summary=`, `description=`, and `tags=[]` to every router and endpoint so the auto-generated Swagger docs at `/docs` are readable. Group endpoints by resource tag. Add example values to key Pydantic schemas using `model_config` or `Field(example=...)`.

**Branch:** `chore/openapi-annotations`
**Commit:** `Add OpenAPI descriptions and examples to all endpoints`

- [ ] Task 12.1 complete

---

### Task 12.2 — Run Linter & Full Test Suite

**Description:**
Run `ruff check .` and fix all linting errors. Run `pytest --cov=app --cov-report=term-missing` and confirm **≥80% coverage** on `services/` and `routers/`. Fix any failing tests. Confirm `alembic upgrade head` runs cleanly on a fresh database. Confirm the seed script runs cleanly after migrations.

**Guidelines to read first:**
- `backend/guidelines/testing.md` — coverage target
- `shared/guidelines/conventions.md` — ruff linting requirement

**Branch:** `chore/lint-and-tests`
**Commit:** `Fix linting errors and achieve ≥80% test coverage`

- [ ] Task 12.2 complete

---

## Implementation Summary

| Phase | Tasks | Status |
|---|---|---|
| Phase 1 — Project Foundation | 5 tasks | 5 / 5 |
| Phase 2 — Database Models | 12 tasks | 12 / 12 |
| Phase 3 — Dependencies & Middleware | 2 tasks | 2 / 2 |
| Phase 4 — Auth Implementation | 4 tasks | 4 / 4 |
| Phase 5 — Core Resource CRUD | 5 tasks | 5 / 5 |
| Phase 6 — Operations | 3 tasks | 3 / 3 |
| Phase 7 — Real-Time Tracking | 2 tasks | 0 / 2 |
| Phase 8 — Arrival Time Estimation | 1 task | 0 / 1 |
| Phase 9 — Superadmin Portal | 1 task | 0 / 1 |
| Phase 10 — Seed & Docker | 2 tasks | 0 / 2 |
| Phase 11 — Tests | 3 tasks | 0 / 3 |
| Phase 12 — Final Polish | 2 tasks | 0 / 2 |
| **Total** | **42 tasks** | **23 / 42** |
