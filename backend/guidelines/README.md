# Backend Guidelines — Index

> Always read the relevant files from `prototype/shared/guidelines/` **first**, then load the backend files you need.

---

## Files in This Directory

| File | What It Covers | Load When... |
|---|---|---|
| [architecture.md](./architecture.md) | Full project folder structure, file naming conventions | Starting backend work, adding a new module or router |
| [patterns.md](./patterns.md) | FastAPI, Pydantic v2, SQLAlchemy 2.x usage rules and patterns | Writing any router, schema, model, or service |
| [realtime.md](./realtime.md) | WebSocket setup, Redis pub/sub, tenant-scoped channels | Anything touching real-time vehicle tracking |
| [database.md](./database.md) | Migrations, soft deletes, audit logging, indexes | Schema changes, new ORM models, Alembic usage |
| [testing.md](./testing.md) | pytest rules, tenant isolation tests, coverage targets | Writing or reviewing tests |
| [config.md](./config.md) | Environment variables, billing config, deployment settings | Setting up environment, adding new config values |

---

## Quick Reference: What to Load by Task

| Task | Shared Files | Backend Files |
|---|---|---|
| New API endpoint | `entities.md`, `api-contracts.md`, `multi-tenancy.md` | `patterns.md`, `architecture.md` |
| New ORM model | `entities.md`, `conventions.md` | `patterns.md`, `database.md` |
| Auth/permissions | `auth.md`, `multi-tenancy.md` | `patterns.md` |
| WebSocket / real-time | `multi-tenancy.md` | `realtime.md` |
| New test file | `multi-tenancy.md` | `testing.md` |
| Alembic migration | `entities.md` | `database.md` |
| Deployment / env setup | — | `config.md` |
