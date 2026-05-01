# Backend — Environment Configuration

> All configuration is loaded from environment variables via `pydantic-settings` in `core/config.py`.
> Never hard-code any value that differs between environments.

---

## Environment Variables

### Core Application

| Variable | Default | Description |
|---|---|---|
| `DEBUG` | `false` | Enables debug mode and verbose logging |
| `SECRET_KEY` | — | JWT signing secret — minimum 32 characters. **Required.** |
| `ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Access token TTL in minutes |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token TTL in days |
| `CORS_ORIGINS` | — | Comma-separated list of allowed frontend origins |

### Database

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | — | PostgreSQL connection string. Example: `postgresql+asyncpg://user:pass@host/db` |

### Cache & Real-Time

| Variable | Default | Description |
|---|---|---|
| `REDIS_URL` | — | Redis connection string. Example: `redis://localhost:6379/0` |

## `.env.example` Template

Maintain an `.env.example` file in the repo root with all variables listed (no real values):

```env
DEBUG=false
SECRET_KEY=your-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
CORS_ORIGINS=http://localhost:5173,https://yourdomain.com

DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/transport_db

REDIS_URL=redis://localhost:6379/0
```

---

## Deployment Reference

| Environment | Frontend | Backend | Database | Cache |
|---|---|---|---|---|
| Development | Vite dev server (port 5173) | `uvicorn main:app --reload` (port 8000) | PostgreSQL (Docker) | Redis (Docker) |
| Production | Nginx serving Vite build | Gunicorn + Uvicorn workers (4) | Managed PostgreSQL (e.g. Supabase, RDS) | Managed Redis (e.g. Upstash) |
