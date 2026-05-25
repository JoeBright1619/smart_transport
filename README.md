# Smart Transport

Smart Transport is a full-stack public transport management system for a multi-tenant fleet operation. It combines a FastAPI backend with a React/Vite frontend for managing vehicles, routes, stops, drivers, trips, alerts, maintenance, analytics, arrivals, authentication, and live vehicle tracking.

## Features

- Multi-tenant authentication with JWT access tokens and HttpOnly refresh-token cookies
- Tenant registration and role-based users
- Vehicle, route, stop, driver, trip, alert, and maintenance APIs
- Dashboard and analytics API responses
- Arrival estimate and WebSocket vehicle tracking endpoints
- Superadmin tenant management endpoints
- React dashboard UI with routing, protected pages, maps, tables, forms, and toast feedback
- Live vehicle tracking map with real-time WebSocket updates
- Analytics page with trend charts, route performance, fleet analysis, and PDF export

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, SQLAlchemy 2, Alembic, Pydantic |
| Database | PostgreSQL |
| Cache / realtime support | Redis |
| Auth | JWT access tokens, HttpOnly refresh-token cookies |
| Frontend | React, Vite, TypeScript, React Router |
| UI | Radix UI, Tailwind CSS, Lucide icons |
| Maps / charts | Leaflet, React Leaflet, Recharts |
| PDF export | jsPDF, jspdf-autotable |
| Tooling | Docker Compose, pytest, Ruff |

## Repository Structure

```text
smart_transport/
  backend/              FastAPI app, routers, schemas, models, migrations, tests
  frontend/             React/Vite frontend application
  docs/                 Architecture, setup, API notes, seed plan, roadmap
  shared/               Shared planning and conventions
  docker-compose.yml    PostgreSQL, Redis, and backend services
```

## Prerequisites

- Node.js 18+
- Docker Desktop
- Git

## Environment Files

Backend — copy the example and leave values as-is for Docker:

```bash
cp backend/.env.example backend/.env
```

> **Important:** Do not change `DATABASE_URL` or `REDIS_URL` in `backend/.env`. Those variables are only read when running the backend outside Docker. The Docker Compose setup injects its own values via `environment:` in `docker-compose.yml` and the backend container connects to the `db` and `redis` services automatically.

Frontend:

```bash
cp frontend/.env.example frontend/.env.local
```

Default frontend values (no changes needed for local development):

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## Quick Start

### 1. Start the backend services

From the repository root:

```bash
docker compose up -d
```

This starts PostgreSQL, Redis, and the FastAPI backend. Services are available at:

| Service | URL |
|---|---|
| API | `http://localhost:8000` |
| API docs (Swagger) | `http://localhost:8000/docs` |
| PostgreSQL | `localhost:5432` |
| Redis | `localhost:6379` |

### 2. Run database migrations

```bash
docker compose exec backend alembic upgrade head
```

### 3. Seed demo data

```bash
docker compose exec backend python -m app.core.seed
```

This seeds 5 tenants, 8 vehicles, 6 routes, 8 drivers, 5 active trips, 90 days of historical trips (~900 records), 90 days of analytics records, maintenance records, and alerts.

> **Warning:** Always run the seed command inside the container using `docker compose exec backend ...`. Running `python -m app.core.seed` directly from your local terminal connects to your local PostgreSQL (if any) instead of the Docker database, and the data will not appear in the app.

### 4. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

## Demo Credentials

After seeding, these accounts are available:

| Role | Email | Password |
|---|---|---|
| Superadmin | `superadmin@platform.local` | `Admin@123456` |
| Admin | `admin@ecofleet.rw` | `Password123!` |
| Operator | `operator@ecofleet.rw` | `Password123!` |
| Dispatcher | `dispatcher@ecofleet.rw` | `Password123!` |
| Passenger | `passenger@ecofleet.rw` | `Password123!` |

## Frontend Integration Status

All 33 frontend–backend integration tasks are complete. The frontend communicates entirely with the real backend API — no mock data remains.

Completed:

- Frontend environment variables and Axios client setup
- Backend-aligned TypeScript types (camelCase throughout)
- JWT injection, token refresh, and session expiry handling
- Auth context, login, register, and logout flows
- All resource service files: users, vehicles, routes, stops, drivers, trips, alerts, maintenance, analytics, arrivals, and superadmin
- All pages connected to real API: Dashboard, Fleet Management, Route Management, Driver Management, Trip Management, Dispatch, Alerts, Maintenance, Analytics, Vehicle Tracking, and Superadmin
- Live WebSocket vehicle tracking
- Analytics PDF export

## Useful Commands

Docker (run from repository root):

```bash
docker compose up -d                                      # start all services
docker compose ps                                         # check running containers
docker compose logs -f backend                            # stream backend logs
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

## Connecting to Databases

**pgAdmin (PostgreSQL):**

1. Open pgAdmin and add a new server.
2. Host: `localhost`, Port: `5432`
3. Database: `transport_db`, Username: `transport`, Password: `transport`

**RedisInsight:**

1. Open RedisInsight and add a new connection.
2. Host: `localhost`, Port: `6379` (no password by default)

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

All JSON field names use camelCase (the backend serializes via response aliases). Interactive OpenAPI docs are available at `http://localhost:8000/docs`.

## More Documentation

- [Development setup](docs/Dev-Setup.md)
- [Architecture](docs/Architecture.md)
- [Tech stack](docs/TechStack.md)
- [MVP scope](docs/MVP-Scope.md)
- [Seed plan](docs/Seed-Plan.md)
- [Roadmap](docs/Roadmap.md)
- [Frontend integration plan](frontend/IMPLEMENTATION.md)
- [Simulation plan](SIMULATION_PLAN.md)

## Development Notes

- Keep `frontend/.env.local` and `backend/.env` local; commit only `.env.example` files.
- Keep files small and focused. Frontend pages should mostly compose smaller components, hooks, and helpers.
- If login fails, check that Docker containers are running (`docker compose ps`), CORS allows `http://localhost:5173`, and seed data has been created with `docker compose exec backend python -m app.core.seed`.
- The `pgdata` Docker volume persists the database across restarts. Use `docker compose down -v` only if you want a clean slate.
