# Shared — Authentication & Authorization

> Rules for identity, roles, JWT structure, and access control across the entire system.

---

## Auth Mechanism

- **JWT Bearer tokens** — short-lived access token (15 min) + long-lived refresh token (7 days)
- The JWT payload **must** contain: `userId`, `tenantId`, `role`
- `superadmin` users have `tenantId: null` in their JWT
- Refresh tokens are opaque, stored server-side (DB or Redis), rotated on each use
- Refresh token is delivered in an **HttpOnly cookie**; access token is returned in the response body and stored in memory (never localStorage)

---

## Role Hierarchy

```
superadmin  ← platform operator (you); cross-tenant
    │
  admin     ← per-tenant company administrator
    │
 operator   ← fleet & driver management
    │
dispatcher  ← trip scheduling & dispatch
    │
passenger   ← read-only public access
```

---

## Access Rules by Role

| Role | What They Can Access |
|---|---|
| `passenger` | Read-only: public routes, stops, arrival times. **No tenant operational data.** |
| `dispatcher` | Read/write: trips, dispatch operations — within their tenant only |
| `operator` | Read/write: vehicles, routes, drivers, stops — within their tenant only |
| `admin` | Full access within their tenant: all modules + user management + configuration |
| `superadmin` | Cross-tenant access to everything. Can create/suspend/reactivate tenants. Can impersonate any tenant admin. **Must be seeded directly in DB — cannot be created from any tenant's admin panel.** |

---

## Endpoint Protection Rules

- All protected endpoints must validate the JWT **and** check `tenant.isActive`
- Role checks use `require_role(*roles)` dependency (backend) or route guards (frontend)
- Returning `403 Forbidden` (not `401`) when a valid user lacks permission
- Never expose: password hashes, raw tokens, internal system IDs in API responses

---

## Superadmin Impersonation

- A `superadmin` may act as a tenant admin for support purposes
- Every impersonation session must create an `AuditLog` entry with `actionType: 'impersonate'`, recording the `superadmin` userId, the target tenant, and timestamp
- The impersonation token must have a short expiry (max 1 hour) and must be clearly differentiated in the JWT payload

---

## Security Rules

- HTTPS only in production; HTTP on localhost only
- CORS: restrict to known frontend origins — wildcard `*` is forbidden in production
- Rate limit all public/unauthenticated endpoints
- Never log passwords, tokens, or GPS coordinates linked to individual passengers
- `tenantId` from the JWT is trusted. Any `tenantId` submitted in a request body or URL by a non-superadmin must be ignored or rejected
