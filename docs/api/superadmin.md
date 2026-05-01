# API Spec — Superadmin

> All endpoints require `role: superadmin`.
> Returns `403 Forbidden` for any other role.
> Base path: `/superadmin` (no `/api/v1` prefix).

---

## `GET /superadmin/tenants`
**Query params:** `?isActive=true&page=1&page_size=20`

**Response `200`:**
```json
{
  "data": [
    {
      "id": "ten-uuid",
      "name": "Kigali Express Ltd",
      "contactEmail": "admin@kigaliexpress.rw",
      "isActive": true,
      "vehicleCount": 12,
      "userCount": 8,
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
    "isActive": true,
    "vehicleCount": 12,
    "userCount": 8,
    "createdAt": "2026-03-01T08:00:00Z",
    "updatedAt": "2026-04-01T10:00:00Z"
  }
}
```

---

## `PATCH /superadmin/tenants/{id}`
Used to suspend/reactivate tenant company accounts.

**Request** (all optional):
```json
{ "isActive": false }
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
    "totalVehicles": 187,
    "totalTripsToday": 432,
    "totalPassengersToday": 17280
  },
  "meta": null
}
```
