# API Spec — Superadmin

> All endpoints require `role: superadmin`.
> Returns `403 Forbidden` for any other role.
> Base path: `/superadmin` (no `/api/v1` prefix).

---

## `GET /superadmin/tenants`
**Query params:** `?isActive=true&tier=pro&page=1&page_size=20`

**Response `200`:**
```json
{
  "data": [
    {
      "id": "ten-uuid",
      "name": "Kigali Express Ltd",
      "contactEmail": "admin@kigaliexpress.rw",
      "subscriptionTier": "pro",
      "isActive": true,
      "vehicleCount": 12,
      "userCount": 8,
      "trialEndsAt": null,
      "createdAt": "2026-03-01T08:00:00Z"
    }
  ],
  "meta": { "total": 5, "page": 1, "pageSize": 20 }
}
```

---

## `GET /superadmin/tenants/{id}`

**Response `200`:**
```json
{
  "data": {
    "id": "ten-uuid",
    "name": "Kigali Express Ltd",
    "contactEmail": "admin@kigaliexpress.rw",
    "billingEmail": "billing@kigaliexpress.rw",
    "subscriptionTier": "pro",
    "vehicleLimit": 100,
    "isActive": true,
    "trialEndsAt": null,
    "vehicleCount": 12,
    "userCount": 8,
    "createdAt": "2026-03-01T08:00:00Z",
    "updatedAt": "2026-04-01T10:00:00Z"
  }
}
```

---

## `PATCH /superadmin/tenants/{id}`
Used to suspend/reactivate tenants or manually override tier.

**Request** (all optional):
```json
{ "isActive": false }
```
```json
{ "subscriptionTier": "enterprise", "vehicleLimit": null }
```
**Response `200`:** Updated tenant object.

---

## `POST /superadmin/tenants/{id}/impersonate`
Creates a short-lived (1 hour) impersonation token for supporting a tenant.
**Always** creates an `AuditLog` entry with `actionType: "impersonate"`.

**Response `200`:**
```json
{ "data": { "accessToken": "<1hr_impersonation_jwt>" } }
```

**Notes:**
- The impersonation JWT payload includes `impersonatedBy: <superadmin_user_id>` to distinguish it from a regular token
- The impersonated session must be clearly labelled in the frontend (e.g., "Viewing as Kigali Express Ltd")

---

## `GET /superadmin/analytics`
Platform-wide aggregated stats across all tenants.

**Query params:** `?from=2026-04-01&to=2026-04-08`

**Response `200`:**
```json
{
  "data": {
    "totalTenants": 12,
    "activeTenants": 11,
    "trialingTenants": 3,
    "totalVehicles": 187,
    "totalTripsToday": 432,
    "totalPassengersToday": 17280
  },
  "meta": null
}
```
