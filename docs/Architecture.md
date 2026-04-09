# Smart Public Transport Tracking & Fleet Management – System Architecture

> **Last updated:** 2026-03-24
> This document describes the target system architecture for both the prototype and production system.

---

## 1. System Overview

The **Smart Public Transport Tracking and Fleet Management System** is a multi-tenant B2B SaaS platform providing real-time visibility, operational control, and data-driven analytics for public transport fleet operations. The prototype reference dataset is based in **Kigali, Rwanda**; the system is geography-agnostic and supports any city or country.

The system serves five actors:
- **Superadmin** — platform operator; manages tenants, billing, and platform-wide analytics
- **Admin** — per-tenant administrator; manages their company's users and configuration
- **Operator** — fleet and driver management within a tenant
- **Dispatcher** — trip scheduling and dispatch within a tenant
- **Passenger** — read-only view of public routes and arrival times

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                         │
│  Browser (React SPA)  ← REST/JSON + WebSocket →  Mobile App │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTPS / WSS
┌───────────────────────────▼─────────────────────────────────┐
│                       API Gateway / Reverse Proxy           │
│                  (Nginx — routing, TLS termination)         │
└──────┬────────────────────┬────────────────────────┬────────┘
       │                    │                        │
┌──────▼──────┐   ┌─────────▼──────────┐  ┌─────────▼───────┐
│  REST API   │   │  WebSocket Server  │  │  Static Files   │
│  (FastAPI)  │   │  (FastAPI + Redis) │  │  (Vite Build)   │
└──────┬──────┘   └─────────┬──────────┘  └─────────────────┘
       │                    │
┌──────▼────────────────────▼──────────────────────────────────┐
│                     Service Layer                             │
│  VehicleService  TripService  DispatchService  AlertService   │
│  DriverService   MaintenanceService  AnalyticsService         │
└──────┬────────────▬──────────────────────────────────────────┘
       │            │
┌──────▼────┐  ┌────▼──────────┐
│PostgreSQL │  │  Redis Cache  │
│  (Primary │  │  (Pub/Sub +   │
│  Database)│  │   Sessions)   │
└───────────┘  └───────────────┘
```

---

## 3. Frontend Architecture

**Type:** Single-Page Application (SPA)
**Framework:** React 18 + TypeScript + Vite

### Component Hierarchy
```
App (RouterProvider)
└── ProtectedRoute
    └── MainLayout
        ├── TopNavigationBar
        ├── SidebarNavigation
        └── <Page> (one of 13 module pages)
            ├── PageHeader
            ├── FilterControlPanel
            ├── DataVisualization (Recharts / Leaflet)
            └── DataTable / List
```

### Key Design Decisions
- **Client-side routing** via React Router v7 (`createBrowserRouter`).
- **Auth state** managed globally through `AuthContext` (React Context API + localStorage token storage).
- **Real-time updates** consumed via a WebSocket hook that feeds vehicle location state.
- **Mock data layer** (`lib/mock-data.ts`) enables the prototype to function without a live backend.
- **Map rendering** via React-Leaflet (OpenStreetMap tiles, no API key required).

### Frontend Module Map
| Module | Route | Components |
|---|---|---|
| Dashboard | `/` | KPI cards, fleet summary chart, alert feed |
| Vehicle Tracking | `/tracking` | Live Leaflet map, vehicle detail panel |
| Fleet Management | `/fleet` | VehicleTable, status badges, add/edit forms |
| Route Management | `/routes` | RouteTable, stop list, route map overlay |
| Arrival Times | `/arrivals` | Stop selector, ETA list, delay indicators |
| Passenger App | `/passenger` | Simplified route/stop view for passengers |
| Dispatch | `/dispatch` | Unassigned trips queue, driver assignment panel |
| Drivers | `/drivers` | DriverList, assignment status, certifications |
| Maintenance | `/maintenance` | MaintenanceLog, scheduled/in-progress/completed |
| Analytics | `/analytics` | Line/bar charts: on-time %, delays, revenue |
| Alerts | `/alerts` | Alert feed, severity filter, acknowledge action |
| Administration | `/admin` | User management, role assignment |
| Security | `/security` | Access control and audit log |

---

## 4. Backend Architecture

**Type:** REST API + WebSocket Server
**Framework:** FastAPI (Python 3.11+)

### Layered Architecture (per feature)
```
Router (HTTP / WS endpoint)
  └── Depends(get_db, get_current_user, require_role)
      └── Service (business logic)
          └── Repository / SQLAlchemy ORM Query
              └── PostgreSQL
```

### Core Modules
| Module | Responsibility |
|---|---|
| `core/config.py` | Environment-based configuration via pydantic-settings |
| `core/database.py` | async SQLAlchemy engine and session management |
| `core/security.py` | JWT creation/verification, bcrypt password hashing |
| `core/dependencies.py` | Reusable FastAPI `Depends()` functions |
| `models/` | ORM table definitions (SQLAlchemy 2.x Mapped API) |
| `schemas/` | Pydantic v2 request/response schemas |
| `routers/` | HTTP route definitions — thin, delegate to services |
| `services/` | Business logic, transaction management, cross-entity coordination |
| `websocket/` | Real-time vehicle position broadcasting |

### API Surface
```
POST   /auth/login              → returns access + refresh tokens
POST   /auth/refresh            → rotate refresh token
POST   /auth/logout

GET    /api/v1/users            (admin only)
POST   /api/v1/users            (admin only)
GET    /api/v1/users/{id}
PATCH  /api/v1/users/{id}

GET    /api/v1/vehicles
POST   /api/v1/vehicles
GET    /api/v1/vehicles/{id}
PATCH  /api/v1/vehicles/{id}
DELETE /api/v1/vehicles/{id}

GET    /api/v1/routes
POST   /api/v1/routes
GET    /api/v1/routes/{id}
PATCH  /api/v1/routes/{id}
DELETE /api/v1/routes/{id}

GET    /api/v1/trips
POST   /api/v1/trips
GET    /api/v1/trips/{id}
PATCH  /api/v1/trips/{id}

GET    /api/v1/drivers
POST   /api/v1/drivers
GET    /api/v1/drivers/{id}
PATCH  /api/v1/drivers/{id}

GET    /api/v1/maintenance
POST   /api/v1/maintenance
GET    /api/v1/maintenance/{id}
PATCH  /api/v1/maintenance/{id}

GET    /api/v1/alerts
POST   /api/v1/alerts/{id}/acknowledge

GET    /api/v1/analytics?from=&to=

WS     /ws/tracking             → real-time vehicle positions (JWT-authenticated)
```

---

## 5. Database Architecture

**Primary DB:** PostgreSQL 15+
**ORM:** SQLAlchemy 2.x with Alembic migrations
**Dev/Test DB:** SQLite (in-memory for unit tests)

### Entity Relationship Diagram (ERD)
```
tenants                                  ← TOP-LEVEL: one row per customer company
 ├── id (PK, UUID, prefix: ten-)
 ├── name
 ├── contact_email
 ├── billing_email
 ├── subscription_tier ENUM('starter','pro','enterprise')
 ├── vehicle_limit (INTEGER: 20 / 100 / NULL)
 ├── is_active (BOOLEAN DEFAULT TRUE)
 ├── trial_ends_at (TIMESTAMP, nullable)
 └── created_at, updated_at

subscriptions
 ├── id (PK, UUID)
 ├── tenant_id (FK → tenants)
 ├── tier ENUM('starter','pro','enterprise')
 ├── status ENUM('active','past_due','cancelled','trialing')
 ├── current_period_start, current_period_end
 ├── external_billing_id (Stripe/Flutterwave subscription ID)
 └── created_at

users
 ├── id (PK, UUID)
 ├── tenant_id (FK → tenants, nullable for superadmin)
 ├── email (UNIQUE)
 ├── password_hash
 ├── full_name
 ├── role ENUM('superadmin','admin','operator','dispatcher','passenger')
 ├── phone
 ├── is_deleted (BOOLEAN DEFAULT FALSE)
 └── created_at, updated_at

vehicles
 ├── id (PK, UUID, prefix: veh-)
 ├── tenant_id (FK → tenants)            ← MANDATORY on all operational tables
 ├── registration_number
 ├── model, capacity
 ├── status ENUM('active','idle','maintenance','offline')
 ├── lat, lng (current location)
 ├── speed, heading, fuel
 ├── engine_status ENUM('good','warning','critical')
 ├── route_id (FK → routes, nullable)
 ├── driver_id (FK → drivers, nullable)
 ├── is_deleted (BOOLEAN DEFAULT FALSE)
 └── created_at, updated_at

routes
 ├── id (PK, UUID, prefix: route-)
 ├── tenant_id (FK → tenants)
 ├── name, number
 ├── distance, duration
 ├── is_active
 ├── color
 ├── is_deleted (BOOLEAN DEFAULT FALSE)
 └── created_at, updated_at

stops
 ├── id (PK, UUID)
 ├── tenant_id (FK → tenants)
 ├── name
 ├── lat, lng
 ├── order
 └── is_deleted (BOOLEAN DEFAULT FALSE)

route_stops (junction)
 ├── route_id (FK → routes)
 ├── stop_id (FK → stops)
 └── stop_order

drivers
 ├── id (PK, UUID, prefix: drv-)
 ├── tenant_id (FK → tenants)
 ├── name, license_number
 ├── phone, rating, total_trips
 ├── status ENUM('available','on-trip','off-duty')
 ├── vehicle_id (FK → vehicles, nullable)
 ├── certification_expiry
 ├── is_deleted (BOOLEAN DEFAULT FALSE)
 └── created_at, updated_at

trips
 ├── id (PK, UUID, prefix: trip-)
 ├── tenant_id (FK → tenants)
 ├── vehicle_id (FK → vehicles)
 ├── route_id (FK → routes)
 ├── driver_id (FK → drivers)
 ├── scheduled_start, actual_start
 ├── scheduled_end, actual_end
 ├── status ENUM('scheduled','active','completed','cancelled')
 ├── passengers, delay
 ├── is_deleted (BOOLEAN DEFAULT FALSE)
 └── created_at, updated_at

maintenance_records
 ├── id (PK, UUID)
 ├── tenant_id (FK → tenants)
 ├── vehicle_id (FK → vehicles)
 ├── type ENUM('routine','repair','inspection')
 ├── description, scheduled_date, completed_date
 ├── cost, status, next_due
 ├── is_deleted (BOOLEAN DEFAULT FALSE)
 └── created_at, updated_at

alerts
 ├── id (PK, UUID)
 ├── tenant_id (FK → tenants)
 ├── type ENUM('delay','breakdown','maintenance','geofence','speeding','info')
 ├── severity ENUM('low','medium','high','critical')
 ├── title, message
 ├── vehicle_id (FK → vehicles, nullable)
 ├── driver_id (FK → drivers, nullable)
 ├── is_acknowledged (BOOLEAN DEFAULT FALSE)
 └── created_at

audit_logs                               ← Immutable. Never soft-delete or update.
 ├── id (PK, UUID)
 ├── tenant_id (FK → tenants, nullable for superadmin actions)
 ├── user_id (FK → users)
 ├── entity_type (VARCHAR — e.g. 'Vehicle', 'Driver')
 ├── entity_id (UUID)
 ├── action_type ENUM('create','update','soft_delete','login','impersonate')
 ├── metadata (JSONB — stores before/after diff or context)
 └── created_at

── INDEXES (Required) ──────────────────────────────────
 idx_vehicles_tenant_id
 idx_routes_tenant_id
 idx_trips_tenant_id
 idx_drivers_tenant_id
 idx_alerts_tenant_id
 idx_audit_logs_tenant_id
 idx_vehicles_status
 idx_trips_status
 idx_alerts_is_acknowledged
```

---

## 6. Real-Time Architecture

```
GPS Feed / Backend Simulation (per tenant)
        │
        ▼
 AlertService.evaluate(tenant_id)  ◄── triggered on each position update
        │
        ▼
  PostgreSQL (persist alert if triggered)
        │
        ▼
  Redis Pub/Sub — tenant-scoped channel
  "vehicle_updates:{tenant_id}"         ← e.g. vehicle_updates:ten-abc123
        │
        ▼
  ConnectionManager
  (stores tenant_id per WebSocket client)
        │  broadcasts ONLY to clients matching tenant_id
        ▼
  React Frontend — tenant-isolated map view
  (updates markers only for the logged-in company's vehicles)
```

- Vehicle positions are updated every **5 seconds**.
- Each tenant's vehicles are broadcast exclusively on their own Redis channel.
- A `superadmin` may subscribe to `vehicle_updates:all` for platform-wide monitoring (disabled in prototype).
- In the prototype phase, the frontend simulates real-time updates with `use-vehicle-simulation.ts`.

---

## 7. Authentication Flow

```
1. Client: POST /auth/login { email, password }
2. Server: verify password hash → issue JWT (15 min) + refresh token (7 days, stored in DB)
3. Server: set refresh token in HttpOnly cookie; return JWT in response body
4. Client: stores JWT in memory (not localStorage); attaches as Bearer header
5. Client: when JWT expires → POST /auth/refresh (cookie sent automatically)
6. Server: validates refresh token → issues new JWT + rotates refresh token
7. Logout: POST /auth/logout → server invalidates refresh token in DB
```

---

## 8. Security Architecture

| Layer | Mechanism |
|---|---|
| Transport | HTTPS (TLS 1.2+) enforced by Nginx |
| Authentication | JWT (HS256) + HttpOnly refresh cookie |
| Authorization | Role-based access control (RBAC) via FastAPI `Depends` |
| Input Validation | Pydantic v2 schemas on all endpoints |
| SQL Injection | SQLAlchemy ORM parameterized queries only |
| XSS | React's default JSX escaping; no `dangerouslySetInnerHTML` |
| CORS | Origin whitelist via FastAPI `CORSMiddleware` |
| Rate Limiting | Nginx `limit_req` for public endpoints |

---

## 9. Deployment Architecture

### Development
```
Frontend:  npm run dev (Vite dev server, port 5173)
Backend:   uvicorn main:app --reload (port 8000)
Database:  PostgreSQL (Docker or local)
Cache:     Redis (Docker)
```

### Production (Recommended)
```
Frontend:  Vite build → static files served by Nginx
Backend:   Gunicorn + Uvicorn workers (4 workers)
Database:  Managed PostgreSQL (e.g., AWS RDS, Render, Supabase)
Cache:     Managed Redis (e.g., Upstash, Redis Cloud)
Proxy:     Nginx (TLS termination, static files, API proxy)
CI/CD:     GitHub Actions → Docker image build → container deployment
```

### Docker Compose (Development Convenience)
```yaml
services:
  frontend:    # Vite dev server
  backend:     # FastAPI + uvicorn
  db:          # postgres:15
  redis:       # redis:7
  nginx:       # reverse proxy (optional in dev)
```

---

## 10. Scalability Considerations

| Concern | Strategy |
|---|---|
| High vehicle count | Redis pub/sub fan-out; WebSocket connection pooling |
| Analytics queries | Pre-aggregated daily summaries; Redis cache (60s TTL) |
| API throughput | Async FastAPI + uvicorn workers; connection pooling (asyncpg) |
| Horizontal scaling | Stateless API workers; shared Redis for WebSocket state |
| Database load | Read replicas for analytics queries; indexes on hot columns |
