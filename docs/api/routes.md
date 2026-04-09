# API Spec — Routes

> **Roles:** All authenticated roles can read. `admin`, `operator` for write operations.

---

## `GET /api/v1/routes`
**Roles:** All authenticated (including `passenger`)
**Query params:** `?isActive=true&page=1&page_size=20`

**Response `200`:** List of route objects, each including embedded `stops[]` array.

```json
{
  "data": [
    {
      "id": "route-uuid",
      "name": "Nyabugogo - Kimironko",
      "number": "101",
      "distance": 12.5,
      "duration": 35,
      "color": "#3B82F6",
      "isActive": true,
      "stops": [
        { "id": "stop-uuid", "name": "Nyabugogo", "lat": -1.9396, "lng": 30.0585, "order": 1 },
        { "id": "stop-uuid-2", "name": "Kimironko", "lat": -1.9441, "lng": 30.1341, "order": 4 }
      ],
      "createdAt": "2026-04-01T08:00:00Z"
    }
  ],
  "meta": { "total": 2, "page": 1, "pageSize": 20 }
}
```

---

## `POST /api/v1/routes`
**Roles:** `admin`, `operator`

**Request:**
```json
{
  "name": "Nyabugogo - Kimironko",
  "number": "101",
  "distance": 12.5,
  "duration": 35,
  "color": "#3B82F6",
  "stops": [
    { "name": "Nyabugogo", "lat": -1.9396, "lng": 30.0585, "order": 1 },
    { "name": "Kacyiru",   "lat": -1.9453, "lng": 30.0907, "order": 2 },
    { "name": "Kimironko", "lat": -1.9441, "lng": 30.1341, "order": 3 }
  ]
}
```
**Response `201`:** Full route object with generated IDs on stops.
**Errors:** `409` duplicate route number.

---

## `GET /api/v1/routes/{id}`
**Roles:** All authenticated.

**Response `200`:** Route with full `stops[]` array.
**Errors:** `404` if not found or belongs to another tenant.

---

## `PATCH /api/v1/routes/{id}`
**Roles:** `admin`, `operator`

**Request** (all optional):
```json
{ "name": "Nyabugogo - Kimironko Express", "isActive": false, "color": "#EF4444" }
```
> If `stops[]` is included, it **replaces all existing stops** for the route.

**Response `200`:** Updated route with stops.

---

## `DELETE /api/v1/routes/{id}`
**Roles:** `admin`

Soft deletes the route.

**Response `204`.**
**Errors:** `409` if route has active or scheduled trips linked to it.
