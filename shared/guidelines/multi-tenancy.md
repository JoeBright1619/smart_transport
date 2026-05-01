# Shared — Multi-Tenancy Rules

> Rules for data ownership and isolation between transport companies.
> For the thesis prototype, a tenant represents the partner bus company or transport operator.

---

## Core Principle

Every transport company that uses this platform is a **tenant**. Their data (vehicles, drivers, routes, trips, alerts) must be completely invisible to all other tenants. A data leak between tenants is the most severe possible bug in this system.

---

## How Tenant Isolation Works

```
JWT Token  →  contains tenantId
    │
get_current_user()  →  extracts user + tenant_id
    │
get_current_tenant()  →  loads Tenant and checks isActive
    │
Service Method  →  receives tenant_id as required parameter
    │
ORM Query  →  WHERE tenant_id = :tenant_id  (MANDATORY on every query)
```

---

## Mandatory Isolation Rules

1. **Never query without a tenant filter.** Every ORM query on operational tables must include `.where(Model.tenant_id == tenant_id)`. No exceptions.
2. **`tenantId` comes from the JWT, never from the request.** Never read `tenantId` from query params, path params, or request body on non-superadmin endpoints.
3. **Validate ownership on GET by ID.** When retrieving a single entity by `id`, verify the record's `tenant_id` matches the requester's. Return `404 Not Found` on mismatch — do not reveal the resource exists in another tenant.
4. **`superadmin` bypasses tenant filters.** When `role == 'superadmin'`, tenant filtering may be omitted. All superadmin actions must still be logged in `audit_logs`.
5. **Active company check on every protected request.** `get_current_tenant` must raise `403 TENANT_INACTIVE` if `tenant.isActive` is `false`, before any business logic runs.

---

## Inactive Tenant Behaviour

When `tenant.isActive` is `false`:
- Protected operational API endpoints return `403 TENANT_INACTIVE`
- `/auth/login` and `/auth/refresh` remain accessible so users can authenticate and see account status
