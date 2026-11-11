# Smart Transport Backend

A Smart Public Transport Tracking and Fleet Management System designed for Kigali.

## Problem Statement

Public transportation in Kigali faces significant operational challenges:
- **Limited real-time visibility**: Passengers lack accurate arrival times and vehicle locations
- **Inefficient fleet management**: Transport operators struggle with manual dispatch, route adherence, and vehicle utilization tracking
- **Poor passenger experience**: No reliable way to track buses, plan journeys, or report issues
- **Maintenance gaps**: Reactive rather than proactive vehicle maintenance leading to unexpected breakdowns
- **Data-driven decision making**: Lack of analytics for route optimization and fleet performance

This system addresses these challenges by providing real-time tracking, automated fleet management, and data-driven insights for transport operators and passengers.

---

## What We Built

### Core Features

**Fleet Management**
- Multi-tenant architecture supporting multiple transport operators
- Real-time vehicle tracking with GPS position updates every 5 seconds
- Vehicle capacity monitoring and occupancy tracking
- Automated maintenance scheduling and alerts
- Driver management and assignment

**Route & Trip Operations**
- Route definition with stops and schedules
- Automated trip lifecycle management (scheduled → active → completed)
- Real-time ETA calculations for passengers
- Trip reconciliation and performance tracking
- Route adherence monitoring with geofence alerts

**Passenger Experience**
- Passenger registration and profile management
- Real-time boarding/alighting tracking
- Live arrival time estimates at stops
- Capacity-based notifications (full/crowded vehicles)
- Passenger analytics and demand patterns

**Real-Time Systems**
- WebSocket-based live vehicle tracking
- Tenant-scoped Redis pub/sub for multi-tenant isolation
- Automated alert generation (delays, breakdowns, maintenance due, speeding, geofence violations)
- Real-time analytics dashboard with fleet KPIs

**Platform Administration**
- Superadmin portal for tenant management
- Tenant suspension/reactivation capabilities
- Cross-tenant analytics and monitoring
- Comprehensive audit logging for all critical operations

**Simulation & Testing**
- Vehicle simulation (`gps_service`) and passenger simulation (`passenger_service`) run as separate services, connected via MQTT.
- 40+ comprehensive test suites ensuring system reliability

---

## Tech Stack

### Core Framework
- **FastAPI 0.111+**: Modern async Python web framework with automatic OpenAPI documentation
- **Python 3.11+**: Leveraging type hints and async/await patterns
- **Uvicorn**: ASGI server with WebSocket support

### Database & ORM
- **PostgreSQL 15+**: Primary relational database
- **SQLAlchemy 2.0**: Modern async ORM with `Mapped` typing API
- **Alembic 1.13+**: Database migration management
- **asyncpg**: High-performance async PostgreSQL driver

### Authentication & Security
- **JWT (python-jose)**: Stateless authentication tokens
- **Passlib + bcrypt**: Password hashing
- **Pydantic v2**: Request/response validation and security
- **Role-based access control**: admin, driver, dispatcher, superadmin

### Real-Time & Caching
- **Redis 5.0+**: Pub/sub for WebSocket fan-out, analytics caching
- **MQTT (Mosquitto)**: Position and occupancy events between the simulation services and backend
- **WebSockets**: Live vehicle tracking, real-time occupancy updates
- **Tenant-scoped channels**: Data isolation across transport operators

### Data Validation
- **Pydantic v2.7+**: Schema validation with strict typing
- **email-validator**: Email format validation
- **Custom validators**: Coordinate bounds, phone formats, capacity constraints

### Testing
- **pytest 8.0+**: Test framework with async support
- **pytest-asyncio**: Async test fixtures
- **pytest-cov**: Code coverage reporting (≥80% on services/routers)
- **httpx**: Async HTTP client for API testing
- **SQLite (in-memory)**: Fast test database

### Development Tools
- **Ruff 0.4+**: Fast Python linter and formatter
- **Pre-commit hooks**: Automated code quality checks

---

## Architecture Highlights

### Multi-Tenancy
Every operational record is scoped to a `tenant_id`, ensuring complete data isolation between transport operators. All list queries enforce tenant filtering at the service layer.

### Soft Deletes
No data is permanently deleted. Records are marked `is_deleted = TRUE` for regulatory compliance and audit trail preservation.

### Audit Logging
All critical operations (user actions, vehicle changes, trip modifications) are logged to an immutable `audit_logs` table with full before/after state.

### Real-Time Architecture
```
gps_service → MQTT: gps/{tenant}/{vehicle}/position → GPSMQTTSubscriber
                                                         ↓
                                              vehicles + telemetry (PostgreSQL)
                                                         ↓
passenger_service ← same position topic                 WebSocket tracking loop
       ↓ stop-arrival detection and boarding/alighting              ↓
MQTT: gps/{tenant}/{vehicle}/occupancy → OccupancyMQTTSubscriber → Redis Pub/Sub
                                               ↓                         ↓
           occupancy events, passenger events, revenue, capacity alert  WebSocket clients
```

The backend does not simulate vehicles or passengers. It consumes MQTT events, persists the resulting state, and publishes tenant-scoped updates through Redis and WebSockets.

### Automated Alert System
- **Low-fuel alerts**: `gps_handler.process_gps_update` detects a transition below 15% fuel
- **Delay alerts**: `gps_handler.process_gps_update` evaluates delay on each GPS position update
- **Breakdown alerts**: `gps_handler.process_gps_update` detects `engine_status: critical`
- **Maintenance alerts**: Service due within 7 days
- **Geofence alerts**: Vehicle >500m outside route corridor
- **Speeding alerts**: `gps_handler.process_gps_update` detects GPS speed above its configured threshold
- **Capacity alerts**: `occupancy_service.record` detects occupancy at the configured threshold

### Service Layer Pattern
All business logic resides in `app/services/`, keeping routers thin and focused on HTTP concerns. Services are injected with database sessions and tenant context.

---

## Project Structure

```
backend/
├── main.py                    # FastAPI app factory, router registration
├── requirements.txt           # Pinned dependencies
├── alembic/                   # Database migrations
├── app/
│   ├── core/                  # Config, database, security, dependencies
│   ├── models/                # SQLAlchemy ORM models (18 entities)
│   ├── schemas/               # Pydantic request/response schemas
│   ├── routers/               # API endpoints (18 routers)
│   ├── services/              # Business logic (27 services)
│   └── websocket/             # Real-time tracking WebSocket handlers
└── tests/                     # 40+ test files, tenant isolation tests
```

See [`guidelines/architecture.md`](guidelines/architecture.md) for the complete structure.

---

## Getting Started

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 5.0+
- MQTT broker (Mosquitto in Docker Compose)

### Installation

1. **Clone and navigate to backend**
```bash
cd backend
```

2. **Create virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your database credentials and secrets
```

5. **Run migrations**
```bash
alembic upgrade head
```

6. **Start development server**
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`
Interactive documentation at `http://localhost:8000/docs`

### Running Tests
```bash
# Run all tests with coverage
pytest --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/test_vehicles.py

# Run tenant isolation tests
pytest tests/test_tenant_isolation.py -v
```

---

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Key Endpoints

**Authentication**
- `POST /auth/login` - User login
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Invalidate refresh token

**Fleet Management**
- `GET/POST /api/v1/vehicles` - List/create vehicles
- `GET /api/v1/vehicles/{id}/latest-arrival-sequence` - Latest passenger-service arrival sequence for a tenant vehicle
- `GET/POST /api/v1/drivers` - Manage drivers
- `GET/POST /api/v1/maintenance` - Maintenance records

**Route Operations**
- `GET/POST /api/v1/routes` - Route definitions
- `GET/POST /api/v1/stops` - Stop/station management
- `GET/POST /api/v1/trips` - Trip scheduling

**Passenger Services**
- `GET /api/v1/passengers` - Cross-tenant passenger pool (superadmin or universal service token)
- `GET /api/v1/arrivals` - Real-time ETAs at stops
- `GET /api/v1/boardings` - Historical legacy boarding records

**Analytics & Monitoring**
- `GET /api/v1/analytics` - Fleet KPIs
- `GET /api/v1/alerts` - System alerts
- `GET /api/v1/audit` - Audit logs

**Real-Time Tracking**
- `WS /ws/tracking?token={jwt}` - Live vehicle positions

**Cross-Service (Universal Token)**
- `GET /api/v1/service/whoami` - Identify a tenant-scoped calling service
- `GET /api/v1/service/routes/{id}` - Get a route across tenants
- `GET /api/v1/service/vehicles` - List active vehicles across tenants
- `GET /api/v1/service/vehicles/{id}` - Get a vehicle across tenants
- `GET /api/v1/service/vehicles/{id}/latest-arrival-sequence` - Get an arrival sequence across tenants

---

## Configuration

All configuration is managed through environment variables (see [`guidelines/config.md`](guidelines/config.md)):

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `REDIS_URL` | Redis connection string | Yes |
| `MQTT_BROKER_URL` | MQTT broker hostname or URL | No (default: `localhost`) |
| `MQTT_BROKER_PORT` | MQTT broker port | No (default: `1883`) |
| `SECRET_KEY` | JWT signing secret (32+ chars) | Yes |
| `CORS_ORIGINS` | Allowed frontend origins (comma-separated) | Yes |
| `DEBUG` | Enable debug mode | No (default: false) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT access token TTL | No (default: 15) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | JWT refresh token TTL | No (default: 7) |

---

## Development Guidelines

Comprehensive guidelines are available in the `guidelines/` directory:

- **[architecture.md](guidelines/architecture.md)**: Project structure, file organization
- **[patterns.md](guidelines/patterns.md)**: FastAPI, Pydantic, SQLAlchemy patterns
- **[database.md](guidelines/database.md)**: Migrations, soft deletes, audit logging
- **[realtime.md](guidelines/realtime.md)**: WebSocket, Redis pub/sub patterns
- **[testing.md](guidelines/testing.md)**: pytest conventions, tenant isolation tests
- **[config.md](guidelines/config.md)**: Environment configuration, deployment

### Key Principles

1. **Multi-tenancy First**: Every query must filter by `tenant_id`
2. **Soft Deletes Only**: Never `DELETE`, always set `is_deleted = TRUE`
3. **Audit Everything**: Log all mutations to `audit_logs`
4. **Test Isolation**: Every resource must have tenant isolation tests
5. **Type Safety**: Leverage Pydantic v2 and SQLAlchemy 2.x typing

---
