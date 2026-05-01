# Shared Guidelines — Index

> These rules apply to **every agent** working anywhere in this system.
> Always check this index first and load only the files relevant to your task.

---

## Files in This Directory

| File | What It Covers | Load When... |
|---|---|---|
| [entities.md](./entities.md) | Canonical domain entity definitions, field names, enums | Adding/changing any data model, writing schemas, understanding the data |
| [api-contracts.md](./api-contracts.md) | REST rules, URL patterns, response envelopes, HTTP status codes | Building or consuming any API endpoint |
| [auth.md](./auth.md) | Roles, JWT structure, RBAC rules, superadmin rules | Anything touching login, permissions, or user access |
| [multi-tenancy.md](./multi-tenancy.md) | Tenant/company isolation and active-account rules | Anything referencing `tenant_id` or company-scoped data |
| [conventions.md](./conventions.md) | Naming rules, code quality, git workflow, documentation standards | Starting any new file, function, or commit |

---

## Quick Reference: What to Load by Task

| Task | Files to Read |
|---|---|
| New API endpoint | `entities.md` + `api-contracts.md` + `multi-tenancy.md` |
| Auth / permissions | `auth.md` + `multi-tenancy.md` |
| New domain entity | `entities.md` + `conventions.md` |
| Code review / naming | `conventions.md` |
| Full system understanding | Read all files |
