# Shared — Multi-Tenancy & Subscription Rules

> Rules for data isolation between tenants and subscription tier enforcement.
> This is the most critical document for commercial correctness.

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
get_current_tenant()  →  loads Tenant, checks isActive + subscription
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
5. **Subscription check on every request.** `get_current_tenant` must raise `403 SUBSCRIPTION_INACTIVE` if `tenant.isActive` is `false`, before any business logic runs.

---

## Subscription Tiers

| Tier | Vehicle Limit | Features Included |
|---|---|---|
| `starter` | 20 | Live tracking, basic alerts (delay, breakdown), route & stop management |
| `pro` | 100 | Everything in Starter + analytics dashboard, maintenance scheduling, driver scoring, SMS/email alerts |
| `enterprise` | Unlimited | Everything in Pro + REST API access, white-label branding, priority support |

---

## Feature Gating Rules

- Use a `require_feature(feature_name)` dependency on gated endpoints:
  ```python
  @router.get("/analytics", dependencies=[Depends(require_feature("analytics"))])
  ```
- Returns `403 FEATURE_NOT_AVAILABLE` if the tenant's tier does not include the feature.
- Feature → tier mapping:
  | Feature Key | Minimum Tier |
  |---|---|
  | `analytics` | `pro` |
  | `maintenance` | `pro` |
  | `driver_scoring` | `pro` |
  | `sms_alerts` | `pro` |
  | `api_access` | `enterprise` |
  | `white_label` | `enterprise` |

---

## Vehicle Limit Enforcement

- Call `tenant_service.check_vehicle_limit(tenant_id)` before creating a new vehicle.
- Count active (non-deleted) vehicles for the tenant and compare to `tenant.vehicleLimit`.
- Return `403 VEHICLE_LIMIT_REACHED` if the limit would be exceeded.

---

## Trial Period

- New tenants get a **14-day free trial** with full `pro` tier access (`status: 'trialing'`).
- When `trialEndsAt` passes with no billing method on file, the tenant is downgraded to `starter`.
- `isActive` remains `true` during trial.

---

## Inactive Tenant Behaviour

When `tenant.isActive` is `false` (subscription cancelled/suspended):
- **All** API endpoints return `403 SUBSCRIPTION_INACTIVE`
- **Exception:** `/auth/login` and `/auth/refresh` remain accessible so users can log in and view their billing status page
