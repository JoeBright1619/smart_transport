# API Spec — Trips

> **Roles:** `admin`, `dispatcher` for write. `operator` read-only.

---

## `GET /api/v1/trips`
**Roles:** `admin`, `operator`, `dispatcher`
**Query params:** `?status=active&vehicleId=veh-uuid&driverId=drv-uuid&routeId=route-uuid&page=1&page_size=20`

**Response `200`:**
```json
{
  "data": [
    {
      "id": "trip-uuid",
      "vehicleId": "veh-uuid",
      "routeId": "route-uuid",
      "driverId": "drv-uuid",
      "scheduledStart": "2026-04-09T08:00:00Z",
      "actualStart": "2026-04-09T08:03:00Z",
      "scheduledEnd": "2026-04-09T08:35:00Z",
      "actualEnd": null,
      "status": "active",
      "passengers": 34,
      "delay": 3,
      "createdAt": "2026-04-08T17:00:00Z"
    }
  ],
  "meta": { "total": 4, "page": 1, "pageSize": 20 }
}
```

---

## `POST /api/v1/trips`
**Roles:** `admin`, `dispatcher`

**Request:**
```json
{
  "vehicleId": "veh-uuid",
  "routeId": "route-uuid",
  "driverId": "drv-uuid",
  "scheduledStart": "2026-04-09T08:00:00Z",
  "scheduledEnd": "2026-04-09T08:35:00Z"
}
```
**Response `201`:** Trip object with `status: "scheduled"`.
**Errors:** `409` if vehicle or driver already has a conflicting active/scheduled trip.

---

## `GET /api/v1/trips/{id}`
**Roles:** `admin`, `operator`, `dispatcher`

**Response `200`:** Single trip object.
**Errors:** `404` if not found or belongs to another tenant.

---

## `PATCH /api/v1/trips/{id}`
**Roles:** `admin`, `dispatcher`

Used for **status transitions only:**

| Body | Effect |
|---|---|
| `{ "status": "active" }` | Starts the trip — sets `actualStart = now` |
| `{ "status": "completed" }` | Ends the trip — sets `actualEnd = now` |
| `{ "status": "cancelled" }` | Cancels the trip |

> `passengers` and `delay` are updated by the backend tracking system, not by this endpoint.

**Valid transitions:**
```
scheduled → active → completed
scheduled → cancelled
active → cancelled
```

**Response `200`:** Updated trip.
**Errors:** `400` for invalid status transitions (e.g., `completed → active`).
