# ⚠️ This file has been split into focused guideline files

This monolithic guidelines file has been replaced by smaller, task-specific files
for better clarity and lower token usage when working with AI agents.

**Read [`README.md`](./README.md) to find the right file for your task.**

## New Files

| File | Covers |
|---|---|
| [README.md](./README.md) | Index — what to load for each task |
| [architecture.md](./architecture.md) | Project folder structure, file naming |
| [patterns.md](./patterns.md) | FastAPI, Pydantic v2, SQLAlchemy patterns |
| [realtime.md](./realtime.md) | WebSocket, Redis, tenant-scoped channels |
| [database.md](./database.md) | Migrations, soft deletes, audit logging, indexes |
| [testing.md](./testing.md) | pytest, tenant isolation tests, coverage |
| [config.md](./config.md) | Environment variables, deployment |

> Also read the relevant files in `prototype/shared/guidelines/` — the shared guidelines
> define entity contracts, API rules, auth, and multi-tenancy that this backend depends on.
