# Development Setup Guide

> **Purpose:** Step-by-step instructions to get the full stack running locally.
> Covers: prerequisites, environment config, database setup, and running the services.

---

## Prerequisites

Ensure the following are installed before starting:

| Tool | Version | Install |
|---|---|---|
| Python | 3.11+ | [python.org](https://python.org) |
| Node.js | 18+ | [nodejs.org](https://nodejs.org) |
| Docker Desktop | Latest | [docker.com](https://docker.com/products/docker-desktop) |
| Git | Any | [git-scm.com](https://git-scm.com) |

---

## 1. Clone the Repository

```bash
git clone <repo-url>
cd "final year project/smart_transport"
```

---

## 2. Start Infrastructure (PostgreSQL + Redis)

A `docker-compose.yml` at the repo root runs PostgreSQL and Redis:

```yaml
# docker-compose.yml
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: transport
      POSTGRES_PASSWORD: transport
      POSTGRES_DB: transport_db
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  pgdata:
```

```bash
# From the repo root
docker compose up -d
```

Verify both are running:
```bash
docker compose ps
```

---

## 3. Backend Setup

```bash
cd backend

# Create and activate virtualenv
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configure Environment Variables

```bash
# Copy the template
cp .env.example .env
```

Edit `backend/.env` with these values for local development:

```env
DEBUG=true
SECRET_KEY=dev-secret-key-change-in-production-32chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
CORS_ORIGINS=http://localhost:5173

DATABASE_URL=postgresql+asyncpg://transport:transport@localhost:5432/transport_db
REDIS_URL=redis://localhost:6379/0

SUPERADMIN_PASSWORD=Admin@123456
SEED_PASSWORD=Password123!
RUN_SEED=true
```

### Run Migrations

```bash
alembic upgrade head
```

### Seed the Database

```bash
python -m app.core.seed
```

Expected output:
```
[seed] Superadmin created: superadmin@platform.local
[seed] Demo tenant created: Kigali Express Ltd (ten-demo-001)
[seed] Users seeded: 4
[seed] Routes seeded: 2 (6 stops total)
[seed] Drivers seeded: 3
[seed] Vehicles seeded: 4
[seed] Maintenance records seeded: 2
[seed] Alerts seeded: 3
[seed] Done.
```

### Start the Backend

```bash
uvicorn main:app --reload --port 8000
```

Backend is running at: `http://localhost:8000`
Interactive API docs: `http://localhost:8000/docs`

---

## 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

Frontend is running at: `http://localhost:5173`

---

## 5. Verify Everything Works

Open `http://localhost:5173` and log in with the demo credentials:

| Role | Email | Password |
|---|---|---|
| Admin | `admin@kigaliexpress.rw` | `Password123!` |
| Operator | `operator@kigaliexpress.rw` | `Password123!` |
| Dispatcher | `dispatcher@kigaliexpress.rw` | `Password123!` |
| Passenger | `passenger@kigaliexpress.rw` | `Password123!` |
| Superadmin | `superadmin@platform.local` | `Admin@123456` |

Check that:
- [ ] Dashboard loads with KPI cards
- [ ] Vehicle Tracking map shows 2 active vehicles
- [ ] WebSocket connection is established (vehicles move every 5 seconds)
- [ ] Alerts page shows 2 unacknowledged alerts

---

## 6. Running Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=term-missing

# Run tenant isolation tests only
pytest tests/test_tenant_isolation.py -v
```

---

## Common Issues

| Problem | Cause | Fix |
|---|---|---|
| `connection refused` on DB | PostgreSQL container not running | `docker compose up -d` |
| `alembic: No module named 'app'` | Virtualenv not activated | Activate `.venv` first |
| Frontend shows old mock data | Backend not connected | Confirm backend is on port 8000; check `VITE_API_URL` in frontend `.env` |
| WebSocket not connecting | Redis not running | `docker compose up -d redis` |
