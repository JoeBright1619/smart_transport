# API Spec — Alerts & Maintenance

---

## Alerts

### `GET /api/v1/alerts`
**Roles:** `admin`, `operator`, `dispatcher`
**Query params:** `?severity=high&type=delay&isAcknowledged=false&page=1&page_size=20`

**Response `200`:**
```json
{
  "data": [
    {
      "id": "alert-uuid",
      "type": "delay",
      "severity": "medium",
      "title": "Trip Delay: RAD 001 A",
      "message": "Vehicle RAD 001 A is 8 minutes behind schedule on Route 101.",
      "vehicleId": "veh-uuid",
      "driverId": "drv-uuid",
      "isAcknowledged": false,
      "createdAt": "2026-04-08T17:01:00Z"
    }
  ],
  "meta": { "total": 3, "page": 1, "pageSize": 20 }
}
```

---

### `POST /api/v1/alerts/{id}/acknowledge`
**Roles:** `admin`, `operator`, `dispatcher`

No request body. Sets `isAcknowledged = true`.

**Response `200`:** Updated alert object.
**Errors:** `404` if not found or belongs to another tenant.

---

## Maintenance

> **Tier gate:** `pro` and `enterprise` only.
> Returns `403 FEATURE_NOT_AVAILABLE` for `starter` tier tenants.

### `GET /api/v1/maintenance`
**Roles:** `admin`, `operator`
**Query params:** `?vehicleId=veh-uuid&status=scheduled&page=1&page_size=20`

**Response `200`:**
```json
{
  "data": [
    {
      "id": "maint-uuid",
      "vehicleId": "veh-uuid",
      "type": "routine",
      "description": "Engine oil change",
      "scheduledDate": "2026-04-15",
      "completedDate": null,
      "cost": 80000,
      "status": "scheduled",
      "nextDue": "2026-07-15",
      "createdAt": "2026-04-08T10:00:00Z"
    }
  ],
  "meta": { "total": 2, "page": 1, "pageSize": 20 }
}
```

---

### `POST /api/v1/maintenance`
**Roles:** `admin`, `operator`

**Request:**
```json
{
  "vehicleId": "veh-uuid",
  "type": "routine",
  "description": "Engine oil change",
  "scheduledDate": "2026-04-15",
  "cost": 80000,
  "nextDue": "2026-07-15"
}
```
**Response `201`:** Maintenance record with `status: "scheduled"`.

---

### `GET /api/v1/maintenance/{id}`
**Response `200`:** Single maintenance record.
**Errors:** `404` if not found or belongs to another tenant.

---

### `PATCH /api/v1/maintenance/{id}`
**Roles:** `admin`, `operator`

**Request** (all optional):
```json
{ "status": "completed", "completedDate": "2026-04-15", "cost": 85000 }
```
> Setting `status: "completed"` automatically sets `completedDate = now` if not provided.

**Response `200`:** Updated maintenance record.
