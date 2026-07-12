# Smart Transport — Backend Defense Prep

> **Goal of this file:** Teach you the backend well enough that in the defense you can (a) explain how the system works, and (b) instantly open the right file when asked "show me where X is implemented."

**Stack:** FastAPI (async) · SQLAlchemy 2.0 async ORM · PostgreSQL (asyncpg) · Redis (pub/sub + cache) · Alembic (migrations) · JWT auth · pytest. It is a **multi-tenant SaaS** — one deployment serves many transport companies ("tenants"), and their data is isolated from each other.

**Root:** `backend/` — entry point `backend/main.py`, app package `backend/app/`.

---

## 1. The 30-second mental model

A request flows like this:

```
HTTP request
  → main.py (CORS, routing, exception envelope)
  → app/routers/<feature>.py        (thin: parse input, check role/tenant, return envelope)
  → app/core/dependencies.py        (get_current_user, get_current_tenant, require_role)
  → app/services/<feature>_service.py  (ALL business logic lives here)
  → app/models/<feature>.py         (SQLAlchemy ORM → PostgreSQL)
  → app/schemas/<feature>.py        (Pydantic validates in, serializes out)
  ← response wrapped in {data, meta, error} envelope
```

**One-liner to memorize:** *"Routers are thin, services hold the logic, models are the tables, schemas are the contract, and everything is scoped to a tenant."*

---

## 2. Directory map (`backend/app/`)

| Folder | What it holds |
|---|---|
| `core/` | Cross-cutting infrastructure: config, database, security, dependencies, geo math, email, seed |
| `models/` | SQLAlchemy ORM models — one file per table |
| `schemas/` | Pydantic request/response models (the API contract) |
| `routers/` | FastAPI `APIRouter` modules — the HTTP endpoints |
| `services/` | Business logic layer (called by routers) |
| `crud/` | Low-level DB helpers (only `analytics.py` — the daily upsert) |
| `websocket/` | Live tracking: WS endpoint, connection manager, vehicle/passenger simulation |
| `../alembic/` | Database migrations (`env.py` + `versions/`) |
| `../tests/` | pytest suite (async, in-memory SQLite) |

> **Note for the panel:** There is **no `dashboard` router** — dashboard numbers come from the `analytics` and `superadmin` routers. There is **no `db/` folder** — DB setup is `app/core/database.py`.

---

## 3. Authentication & Security — *the most-asked topic*

### The files
- **`app/core/security.py`** — the crypto core:
  - `hash_password()` / `verify_password()` — bcrypt via passlib.
  - `create_access_token(data, expires_delta)` — signs an **HS256 JWT** carrying `userId`, `tenantId`, `role` (+ tenant branding).
  - `decode_access_token(token)` — verifies and decodes.
- **`app/core/dependencies.py`** — request-time gatekeepers (these are FastAPI *dependencies*):
  - `get_current_user()` — reads the `Bearer` token, decodes it, loads the non-deleted `User`, and checks the token's role/tenant still match the DB.
  - `get_current_tenant()` — resolves the tenant and **rejects suspended tenants** (`is_active=False`). This is the multi-tenancy gate.
  - `require_role(*roles)` — a dependency *factory*; each router uses e.g. `Depends(require_role("admin","operator"))`.

### The two-token model (know this cold)
- **Access token** = short-lived JWT (**15 min**), sent in the `Authorization: Bearer` header, stateless.
- **Refresh token** = long-lived (**7 days**), stored as an **HttpOnly cookie** (path `/auth`), and its **sha256 hash** is stored in the `refresh_tokens` table. It is **rotated** on every refresh (old one revoked, new one issued).
- Refresh logic is in `app/routers/auth.py`: `_create_refresh_token()`, `_token_hash()`, `_set_refresh_cookie()`, `_get_refresh_token_record()`.

**Why HttpOnly cookie for refresh + localStorage for access?** The refresh token is the powerful long-lived credential, so it's kept out of JavaScript's reach (mitigates XSS token theft). The access token is short-lived, so leaking it is low-risk.

### Role hierarchy
Roles: `superadmin > admin > operator > dispatcher > passenger`.
Ranking + enforcement is in **`app/services/user_service.py`** (`ROLE_RANKS`, `get_role_rank()`) — a user cannot create/edit/delete a user of higher or equal rank than themselves.

### Multi-tenancy enforcement (know this cold)
Every tenant-scoped service query filters `WHERE tenant_id == tenant.id`, where the tenant comes from `get_current_tenant()`. So even if user A guessed user B's vehicle ID from another company, the query returns nothing. Superadmin endpoints **deliberately** bypass this to see across tenants. Proof it works: **`tests/test_tenant_isolation.py`**.

### Other security flows
- **Invitations** — `user_service.create_user` (invite branch) mints a 48-hour JWT (`type:"invite"`), stores its hash; `accept_invitation()` validates token + hash + status. Email sent via `app/core/email.py`.
- **Passenger OTP** — `app/services/passenger_service.py`: `register_passenger` → email OTP → `verify_email_otp` → account activated. `resend_otp` is rate-limited (60s).
- **Impersonation** — `app/services/superadmin_service.py` `impersonate_tenant_admin()` mints a 1-hour token as the tenant's admin with an `impersonatedBy` claim; the action is audited.
- **WebSocket auth** — `app/websocket/tracking.py` `_authenticate_tracking_connection()` decodes the `?token=` query param (WS can't send headers easily) and re-checks the user/tenant are active.

---

## 4. API routers & endpoints (`app/routers/`)

All registered in `main.py` `create_app()`. Every response uses the envelope `{data, meta, error}` (`app/schemas/common.py`).

| Router (file) | Prefix | Key endpoints |
|---|---|---|
| `auth.py` | `/auth` | register, login, refresh, logout, register/passenger, verify-email, resend-otp |
| `users.py` | `/api/v1/users` | list/create/get/update/delete users, `POST /accept-invite` (no auth) |
| `passengers.py` | `/api/v1/passengers` | `/me`, `/me/stats`, `/me/notifications`, `/operators`, list |
| `boardings.py` | `/api/v1/boardings` | list boardings, `/me` (own history) |
| `vehicles.py` | `/api/v1/vehicles` | CRUD + `GET /{id}/occupancy` |
| `routes.py` | `/api/v1/routes` | CRUD (updating `stops` replaces the ordered list) |
| `stops.py` | `/api/v1/stops` | `GET /public` (no auth), list, create |
| `drivers.py` | `/api/v1/drivers` | CRUD (delete blocked if on a trip) |
| `trips.py` | `/api/v1/trips` | CRUD + lifecycle `scheduled→active→completed/cancelled` |
| `alerts.py` | `/api/v1/alerts` | list + `POST /{id}/acknowledge` |
| `maintenance.py` | `/api/v1/maintenance` | CRUD |
| `analytics.py` | `/api/v1/analytics` | summary, `/report` (route/daily/fleet/driver), `/passenger-report` |
| `arrivals.py` | `/api/v1/arrivals` | tenant ETAs, `/public` (cross-tenant, for passengers) |
| `audit.py` | `/api/v1/audit-logs` | list (admin only) |
| `superadmin.py` | `/superadmin` | tenants list/detail/update, impersonate, passengers, platform analytics |
| `websocket/tracking.py` | — | `WS /ws/tracking` live vehicle stream |

**Exam tip:** if asked "where is login?" → `app/routers/auth.py` `login()`. "How is a role enforced?" → `require_role()` in `app/core/dependencies.py`.

---

## 5. Database models (`app/models/`)

All inherit `Base` (from `app/core/database.py`). PKs are **prefixed UUID strings** (e.g. `veh-<uuid>`, `ten-<uuid>`) — this makes IDs self-describing in logs.

| Model | Table | What it is |
|---|---|---|
| `Tenant` | `tenants` | A transport company. The root of multi-tenancy. |
| `User` | `users` | Staff/passenger accounts. Has `role`, `status`, OTP fields, `invitation_token_hash`. `tenant_id` is null for superadmins. |
| `RefreshToken` | `refresh_tokens` | Hashed refresh tokens (rotation/revocation). |
| `Vehicle` | `vehicles` | Bus: registration, capacity, live lat/lng/speed/fuel, status, occupancy. |
| `Route` / `Stop` / `RouteStop` | `routes`/`stops`/`route_stops` | `RouteStop` is the **ordered join table** (composite PK + `stop_order`). |
| `Driver` | `drivers` | Driver + license, rating, status, assigned vehicle. |
| `Trip` | `trips` | A journey: vehicle+route+driver, scheduled/actual times, status. |
| `Alert` | `alerts` | delay/breakdown/maintenance/geofence/speeding/capacity/info alerts. |
| `MaintenanceRecord` | `maintenance_records` | Service records (routine/repair/inspection). |
| `AnalyticsRecord` | `analytics` | Daily rollup (fuel, revenue) — unique on (tenant, date). |
| `Telemetry` | `telemetry` | Time-series GPS history per vehicle. |
| `AuditLog` | `audit_logs` | Immutable action log (login, impersonate, invite, CRUD…). |
| `PassengerProfile` | `passenger_profiles` | Passenger prefs: favourite routes/stops, notification settings. |
| `BoardingRecord` | `boarding_records` | Boarded/alighted events (feeds occupancy + passenger reports). |

**Relationship to know:** a Route has many Stops **through** `RouteStop`, and the `stop_order` column is what makes ETA calculation possible (you walk stops in order).

---

## 6. Business logic — services (`app/services/`)

Routers are thin; **this is where you point when asked "where is the logic?"**

| Service | Responsibility |
|---|---|
| `vehicle_service.py` | Vehicle CRUD; delete blocked while active. |
| `route_service.py` | Route + stop CRUD; `_replace_route_stops`, cross-tenant public stop list. |
| `driver_service.py` | Driver CRUD; delete blocked while on trip. |
| `trip_service.py` | Trip CRUD + **lifecycle transition validation**. |
| `maintenance_service.py` | Maintenance CRUD. |
| `alert_service.py` | `get_alerts`, `acknowledge_alert`, `auto_generate()` (rule engine), `create_capacity_alert()`. |
| **`arrival_service.py`** | **ETA estimation** (see §8). |
| **`analytics_service.py`** | KPI summary (**Redis-cached 60s**), filtered reports, passenger report. |
| `passenger_service.py` | Registration/OTP, profile CRUD, notifications, operator list. |
| `passenger_stats_service.py` | Passenger trip stats. |
| `passenger_report_service.py` | Superadmin passenger usage report. |
| `boarding_service.py` | Record boardings, list history, trigger capacity alerts. |
| `user_service.py` | User CRUD + **role-rank enforcement** + invitations. |
| `tenant_service.py` | Atomic tenant + first-admin creation, suspend/reactivate. |
| `superadmin_service.py` | Cross-tenant management, impersonation, platform analytics. |
| `audit_service.py` | `log()` (immutable insert), `list_logs()`. |
| **`simulation_runner.py`** | Background loop that "drives" the buses (see §7). |

---

## 7. Real-time tracking & the simulation engine (`app/websocket/`)

Because there are no real GPS devices, the backend **simulates** buses moving along routes. This is a signature feature — expect questions.

- **`simulation_runner.py`** — started in `main.py`'s lifespan. Every **5 seconds** (`TICK_SECONDS`) it advances every active vehicle, writes `Telemetry`, raises low-fuel alerts, and upserts daily fuel analytics.
- **`route_simulation.py`** — the movement math: `advance_vehicle()` moves a bus toward its next stop using **bearing + haversine** (`app/core/geo_math.py`), handles dwell time at stops, burns fuel, and starts/completes trips.
- **`passenger_simulation.py`** — boards/alights passengers at stops, computes fare revenue, persists boarding records, updates occupancy.
- **`manager.py`** — `ConnectionManager`: keeps per-tenant WebSocket connections and uses **Redis pub/sub** (channel `vehicle_updates:{tenant_id}`) to fan updates out. This is what lets the app scale across multiple server processes.
- **`tracking.py`** — the `/ws/tracking` endpoint; authenticates the socket, then pushes vehicle position/occupancy/ETA every 5s.

**Why Redis pub/sub here?** If you run 3 backend workers, a browser is connected to only one of them. The simulation update might be produced on a different worker. Publishing to Redis and having every worker subscribe means all connected browsers get the update regardless of which worker they're on.

---

## 8. ETA / arrivals — how it's computed (`app/services/arrival_service.py`)

`get_arrivals_for_stop()`:
1. Find vehicles serving the route that includes the target stop.
2. From the vehicle's current position/segment, walk the **ordered** route stops (`RouteStop.stop_order`) up to the target stop.
3. Sum the **haversine** distances between consecutive stops (`_route_distance_to_stop_km`).
4. `ETA = distance / current_speed`. Live occupancy is read from the simulation state.

`get_cross_tenant_arrivals()` powers the public passenger view (`/arrivals/public`) and includes the operator (tenant) name.

---

## 9. Database setup & migrations

- **`app/core/database.py`** — async engine (`create_async_engine`, `pool_pre_ping`), `AsyncSessionLocal`, `Base`, and the `get_db()` dependency that yields one session per request.
- **Alembic** — config `backend/alembic.ini`; `backend/alembic/env.py` runs **async** migrations and imports `app.models` so `Base.metadata` is complete.
- **Migrations** — `backend/alembic/versions/` (`0001`→`0017`). To create one: `alembic revision --autogenerate -m "..."`; to apply: `alembic upgrade head`.

---

## 10. Config & seeding

- **`app/core/config.py`** — `Settings(BaseSettings)` loaded from `backend/.env`. Keys: `SECRET_KEY`, `ALGORITHM` (HS256), `ACCESS_TOKEN_EXPIRE_MINUTES` (15), `REFRESH_TOKEN_EXPIRE_DAYS` (7), `CORS_ORIGINS`, `DATABASE_URL`, `REDIS_URL`, SMTP settings, `EMAIL_BACKEND`.
- **`app/core/seed.py`** — seeds a demo tenant, a superadmin, and historical trips/analytics using a **fixed RNG (seed 42)** so demo data is reproducible.

---

## 11. `main.py` — how the app is assembled

`create_app()`:
1. Builds the `FastAPI` app with OpenAPI tag metadata.
2. **Lifespan**: on startup runs `SELECT 1` (DB check) + `start_vehicle_simulation()`; on shutdown stops the sim + disposes the engine.
3. **CORS** middleware from `settings.CORS_ORIGINS`, credentials allowed.
4. Registers all routers.
5. **Exception handlers** convert every error into the `{data, meta, error:{code,message}}` envelope (`HTTPException`, validation errors → `VALIDATION_ERROR`, catch-all → `INTERNAL_SERVER_ERROR` with the message hidden unless `DEBUG`).

---

## 12. Tests (`backend/tests/`)

- **`conftest.py`** — in-memory SQLite (`sqlite+aiosqlite:///:memory:`), fixtures for `db`, `client` (httpx against the ASGI app with `get_db` overridden), `auth_headers()` (mints a JWT), and entity factories.
- **27 test modules** covering auth/JWT, RBAC, every CRUD feature, **tenant isolation**, ETA/arrivals, capacity alerts, boarding simulation, WebSocket occupancy, and superadmin flows.
- Run: `cd backend && pytest`.

---

## 13. Redis usage — exactly two places

1. **WebSocket pub/sub** (`app/websocket/manager.py`) — fan out vehicle updates across workers.
2. **Analytics cache** (`app/services/analytics_service.py`) — `get_analytics()` caches under `analytics:{tenant}:{from}:{to}` for **60s**, and **fails open** (works without Redis, just uncached).

---

## 14. Likely exam questions → where to point

| Question | Answer / file |
|---|---|
| "Walk me through login." | `routers/auth.py login()` → `security.verify_password` → `create_access_token` + set refresh cookie. |
| "How do you keep companies' data separate?" | `get_current_tenant()` + `tenant_id` filter in every service; `test_tenant_isolation.py`. |
| "What happens when the access token expires?" | Frontend calls `/auth/refresh` with the HttpOnly cookie; `auth.py refresh()` rotates it. |
| "How are passwords stored?" | bcrypt hash via `security.hash_password`; never plaintext. |
| "How do buses move on the map?" | Simulation: `simulation_runner.py` → `route_simulation.advance_vehicle()` using `geo_math`. |
| "How is an ETA calculated?" | `arrival_service.py` — sum haversine distances over ordered stops ÷ speed. |
| "How does real-time reach the browser?" | `/ws/tracking` + `ConnectionManager` + Redis pub/sub. |
| "How do you prevent a dispatcher from deleting an admin?" | Role ranks in `user_service.py`. |
| "Where are the DB migrations?" | `backend/alembic/versions/`. |
| "How are errors returned consistently?" | Exception handlers in `main.py` → `{data, meta, error}` envelope. |

---

### Fastest way to demo any backend feature live
Open the interactive API docs at **`http://localhost:8000/docs`** (FastAPI Swagger UI) — every endpoint is listed, grouped by tag, and you can execute requests right there.
