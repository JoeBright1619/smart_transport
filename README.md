# Smart Transport

Smart Transport is a full-stack public transport management system for a multi-tenant fleet operation. It combines a FastAPI backend with a React/Vite frontend for managing vehicles, routes, stops, drivers, trips, alerts, maintenance, analytics, arrivals, authentication, and live vehicle tracking.

The project is built as a final-year project and is currently in the backend-integration phase: the backend API is implemented, the frontend UI exists, and frontend screens are being connected to the backend incrementally.

## Features

- Multi-tenant authentication with JWT access tokens and HttpOnly refresh-token cookies
- Tenant registration and role-based users
- Vehicle, route, stop, driver, trip, alert, and maintenance APIs
- Dashboard and analytics API responses
- Arrival estimate and WebSocket vehicle tracking endpoints
- Superadmin tenant management endpoints
- React dashboard UI with routing, protected pages, maps, tables, forms, and toast feedback

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
| Tooling | Docker Compose, pytest, Ruff |

## Repository Structure

```text
smart_transport/
  backend/              FastAPI app, routers, schemas, models, migrations, tests
  frontend/             React/Vite frontend application
  docs/                 Architecture, setup, API notes, seed plan, roadmap
  shared/               Shared planning and conventions
  docker-compose.yml    Local PostgreSQL, Redis, and backend services
```

## Prerequisites

- Python 3.11+
- Node.js 18+
- Docker Desktop
- Git

## Environment Files

Backend:

```bash
cp backend/.env.example backend/.env
```

Frontend:

```bash
cp frontend/.env.example frontend/.env.local
```

Default frontend values:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## Quick Start With Docker

From the repository root:

```bash
docker compose up -d
```

This starts PostgreSQL, Redis, and the backend API on:

- API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

Then start the frontend separately:

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at:

```text
http://localhost:5173
```

## Manual Backend Setup

Start PostgreSQL and Redis:

```bash
docker compose up -d db redis
```

Create and activate a Python virtual environment:

```bash
cd backend
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS / Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run migrations:

```bash
alembic upgrade head
```

Seed demo data:

```bash
python -m app.core.seed
```

Start the backend:

```bash
uvicorn main:app --reload --port 8000
```

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Build for production:

```bash
npm run build
```

Preview the production build:

```bash
npm run preview
```

## Demo Credentials

After seeding, these accounts are available:

| Role | Email | Password |
|---|---|---|
| Superadmin | `superadmin@platform.local` | `Admin@123456` |
| Admin | `admin@kigaliexpress.rw` | `Password123!` |
| Operator | `operator@kigaliexpress.rw` | `Password123!` |
| Dispatcher | `dispatcher@kigaliexpress.rw` | `Password123!` |
| Passenger | `passenger@kigaliexpress.rw` | `Password123!` |

## Current Frontend Integration Status

The backend is implemented and exposes the API surface. The frontend is being connected in phases from `frontend/IMPLEMENTATION.md`.

Completed so far:

- Frontend environment variables
- Axios installation
- Backend-aligned API TypeScript types
- Shared Axios API client with JWT injection and refresh handling
- Auth service for register, login, refresh, and logout
- Auth context migrated away from mock localStorage auth

Still in progress:

- Register page tenant-registration UX
- Resource service files for users, vehicles, routes, drivers, trips, alerts, maintenance, analytics, arrivals, and superadmin
- Replacing page-level mock data with real API calls
- Live WebSocket tracking integration
- Final removal of `mock-data.ts`

## Useful Commands

Backend:

```bash
cd backend
pytest
pytest --cov=app --cov-report=term-missing
ruff check .
alembic upgrade head
python -m app.core.seed
uvicorn main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
npm run build
npm run preview
```

Docker:

```bash
docker compose up -d
docker compose ps
docker compose logs -f backend
docker compose down
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

Interactive OpenAPI docs are available at:

```text
http://localhost:8000/docs
```

## More Documentation

- [Development setup](docs/Dev-Setup.md)
- [Architecture](docs/Architecture.md)
- [Tech stack](docs/TechStack.md)
- [MVP scope](docs/MVP-Scope.md)
- [Seed plan](docs/Seed-Plan.md)
- [Roadmap](docs/Roadmap.md)
- [Frontend backend-integration plan](frontend/IMPLEMENTATION.md)

## Notes For Development

- Work can be done directly on the current branch for a solo workflow.
- Keep `frontend/.env.local` and `backend/.env` local; commit only `.env.example` files.
- The frontend still contains mock data while migration is in progress. Remove it only after every page has been connected to backend services.
- Keep files small and focused. Frontend pages should mostly compose smaller components/hooks/helpers and should be split before they grow beyond the guideline limit.
- If login fails, check that the backend is running on port `8000`, CORS allows `http://localhost:5173`, and the seed data has been created.
