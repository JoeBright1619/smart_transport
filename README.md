# Smart Transport

A multi-tenant public transport management system built as a three-service
distributed system: a FastAPI backend, two microservices (`gps_service`,
`passenger_service`) connected by MQTT, and a React/Vite frontend.

The system simulates a fleet of buses moving along routes in real time,
tracks their positions, and derives passenger occupancy at each stop — all
persisted to Postgres and broadcast to a live map over WebSocket.

## What it demonstrates

- **Distributed data pipeline.** `gps_service` publishes vehicle positions to
  MQTT every 5 seconds; `passenger_service` consumes those positions, detects
  stop arrivals, simulates passenger boarding/alighting, and publishes
  occupancy events; the backend consumes both streams, persists them
  idempotently, and fans out WebSocket updates via Redis pub/sub.
- **Multi-tenant SaaS architecture.** Every operational record is scoped to a
  `tenant_id`. Auth supports five roles (superadmin, admin, operator,
  dispatcher, passenger), with tenant-scoped and universal service tokens for
  cross-tenant consumers.
- **Async Python throughout.** FastAPI + SQLAlchemy 2.0 async + asyncpg +
  paho-mqtt, with an async test suite on in-memory SQLite.
- **Real-time dashboard.** React + TypeScript + Leaflet with a WebSocket-driven
  live vehicle map, analytics charts, and PDF export.

See [`docs/Architecture.md`](docs/Architecture.md) for the full design and
[`docs/Architecture.md#12-known-gaps-after-phase-5`](docs/Architecture.md#12-known-gaps-after-phase-5)
for what's intentionally out of scope.

## Features

- Multi-tenant authentication with JWT access tokens and HttpOnly refresh-token cookies
- Role-based user management (superadmin / admin / operator / dispatcher / passenger)
- Vehicle, route, stop, driver, trip, alert, and maintenance APIs
- Dashboard and analytics endpoints with trend and fleet-performance breakdowns
- Arrival estimates (ETA at any stop, per active vehicle)
- WebSocket live vehicle tracking with Redis-backed multi-tenant fan-out
- Automated alert generation (low-fuel, delay, speeding, breakdown, capacity)
- Passenger occupancy derived from a real MQTT pipeline
- Superadmin tenant management, impersonation, and audit logging
- React dashboard with maps, charts, tables, forms, and PDF export

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, SQLAlchemy 2 (async), Alembic, Pydantic v2 |
| Database | PostgreSQL 15 |
| Cache / real-time | Redis 7 (pub/sub + caching) |
| Event transport | MQTT (Eclipse Mosquitto) |
| Auth | JWT access tokens, HttpOnly refresh-token cookies |
| Frontend | React 18, Vite, TypeScript, React Router |
| UI | Radix UI, Tailwind CSS, Lucide icons |
| Maps / charts | Leaflet, React Leaflet, Recharts |
| PDF export | jsPDF, jspdf-autotable |
| Services | FastAPI (×3), paho-mqtt, aiohttp |
| Tooling | Docker Compose, pytest, Ruff |

## Repository Structure

```text
smart_transport/
  backend/              FastAPI app, routers, schemas, models, migrations, tests
  frontend/             React/Vite frontend application
  gps_service/          Vehicle simulation, MQTT position publisher
  passenger_service/    Passenger simulation, MQTT occupancy publisher
  docs/                 Architecture, setup, API notes, seed plan, roadmap
  shared/               Shared planning and conventions
  docker-compose.yml    Six services: backend, gps_service, passenger_service,
                        PostgreSQL, Redis, MQTT
```

## Prerequisites

- Docker Desktop
- Node.js 18+ (for local frontend development only — the frontend can also
  run against the dockerized backend)
- Git

## Quick Start

### 1. Start the backend services

From the repository root:

```bash
docker compose up -d
```

This starts PostgreSQL, Redis, MQTT, the FastAPI backend, `gps_service`, and
`passenger_service`. Services are available at:

| Service | URL |
|---|---|
| API | `http://localhost:8000` |
| API docs (Swagger) | `http://localhost:8000/docs` |
| GPS service | `http://localhost:8001` |
| Passenger service | `http://localhost:8002` |
| PostgreSQL | `localhost:5432` |
| Redis | `localhost:6379` |
| MQTT | `localhost:1883` (WebSocket MQTT: `localhost:9001`) |

Wait for containers to report healthy:

```bash
docker compose ps
```

### 2. Run database migrations

```bash
docker compose exec backend alembic upgrade head
```

### 3. Seed demo data

```bash
docker compose exec backend python -m app.core.seed
```

This seeds 5 tenants, 8 vehicles, 6 routes, 8 drivers, 5 active trips, 90
days of historical trips, 90 days of analytics, maintenance records, and
alerts.

> **Note:** Always run the seed command inside the container using
> `docker compose exec backend ...`. Running `python -m app.core.seed` from
> your local terminal connects to your local PostgreSQL, not the Docker one.

### 4. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`. It connects to the backend at
`http://localhost:8000` and the WebSocket at `ws://localhost:8000`.

Within ~10 seconds of the backend services starting, the live map on the
Vehicle Tracking page should show buses moving along their routes, with
occupancy updates arriving at each stop.

### 5. (Optional) Explore the services

```bash
# GPS service status
curl http://localhost:8001/status

# Passenger service status
curl http://localhost:8002/status

# Watch positions flow through MQTT
docker compose exec mqtt mosquitto_sub -h localhost -t 'gps/+/+/position' -v
```

## Demo Credentials

After seeding, these accounts are available:

| Role | Email | Password |
|---|---|---|
| Superadmin | `superadmin@platform.local` | `Admin@123456` |
| Admin | `admin@ecofleet.rw` | `Password123!` |
| Operator | `operator@ecofleet.rw` | `Password123!` |
| Dispatcher | `dispatcher@ecofleet.rw` | `Password123!` |
| Passenger | `passenger@ecofleet.rw` | `Password123!` |

> These credentials are demo-only and stored as plaintext in the seed script.
> Rotate them before deploying anywhere accessible from the internet.

## Useful Commands

Docker (run from repository root):

```bash
docker compose up -d                                      # start all services
docker compose ps                                         # check running containers
docker compose logs -f backend                            # stream backend logs
docker compose logs -f passenger_service                  # stream passenger-service logs
docker compose down                                       # stop all services
docker compose down -v                                    # stop and delete volumes (wipes database)
```

Database migrations (inside container):

```bash
docker compose exec backend alembic upgrade head          # apply all migrations
docker compose exec backend alembic current               # show current revision
docker compose exec backend alembic history               # show migration history
```

Seed and test data (inside container):

```bash
docker compose exec backend python -m app.core.seed       # seed demo data
docker compose exec backend pytest                        # run test suite
docker compose exec backend pytest --cov=app --cov-report=term-missing
docker compose exec backend ruff check .                  # lint check
```

Frontend (run from `frontend/` directory):

```bash
npm install        # install dependencies
npm run dev        # start dev server at http://localhost:5173
npm run build      # production build
npm run preview    # preview production build locally
npm run typecheck  # TypeScript type check
```

## API Notes

Backend responses use a consistent envelope:

```ts
{
  data: T;
  meta?: {
    total: number;
    page: number;
    pageSize: number;
  };
  error?: {
    code: string;
    message: string;
  };
}
```

All JSON field names use camelCase (the backend serializes via response
aliases). Interactive OpenAPI docs are available at
`http://localhost:8000/docs`.

## Documentation

- [Architecture overview](docs/Architecture.md)
- [Known gaps](docs/Architecture.md#12-known-gaps-after-phase-5)
- [Development setup](docs/Dev-Setup.md)
- [Tech stack](docs/TechStack.md)
- [API reference](docs/API-Spec.md)
- [MVP scope](docs/MVP-Scope.md)
- [Seed plan](docs/Seed-Plan.md)
- [Roadmap](docs/Roadmap.md)

## Connecting to Databases

**pgAdmin (PostgreSQL):**

1. Open pgAdmin and add a new server.
2. Host: `localhost`, Port: `5432`
3. Database: `transport_db`, Username: `transport`, Password: `transport`

**RedisInsight:**

1. Open RedisInsight and add a new connection.
2. Host: `localhost`, Port: `6379` (no password by default)

**MQTT Explorer (or any MQTT client):**

1. Connect to `localhost:1883`.
2. Subscribe to `gps/+/+/position` to watch vehicle position events.
3. Subscribe to `gps/+/+/occupancy` to watch occupancy events.

## Development Notes

- Keep `frontend/.env.local`, `backend/.env`, and `passenger_service/.env`
  local; commit only `.env.example` files.
- If login fails, check that all Docker containers are running
  (`docker compose ps`), CORS allows `http://localhost:5173`, and seed data
  was created with `docker compose exec backend python -m app.core.seed`.
- The `pgdata` Docker volume persists the database across restarts. Use
  `docker compose down -v` only if you want a clean slate.

## License

MIT — see [LICENSE](LICENSE).
