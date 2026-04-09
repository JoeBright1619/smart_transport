# API Spec — Vehicles

> **Roles:** `admin`, `operator` for write operations. `dispatcher` read-only.

---

## `GET /api/v1/vehicles`
**Roles:** `admin`, `operator`, `dispatcher`
**Query params:** `?status=active&routeId=route-uuid&page=1&page_size=20`

**Response `200`:**
```json
{
  "data": [
    {
      "id": "veh-uuid",
      "registrationNumber": "RAD 001 A",
      "model": "Yutong ZK6120",
      "capacity": 60,
      "status": "active",
      "currentLocation": { "lat": -1.9450, "lng": 30.0907 },
      "speed": 35,
      "heading": 90,
      "fuel": 75,
      "engineStatus": "good",
      "routeId": "route-uuid",
      "driverId": "drv-uuid",
      "lastUpdate": "2026-04-08T17:00:00Z"
    }
  ],
  "meta": { "total": 6, "page": 1, "pageSize": 20 }
}
```

---

## `POST /api/v1/vehicles`
**Roles:** `admin`, `operator`

**Request:**
```json
{
  "registrationNumber": "RAD 007 G",
  "model": "Yutong ZK6120",
  "capacity": 60,
  "status": "idle"
}
```
**Response `201`:** Vehicle object.
**Errors:** `403 VEHICLE_LIMIT_REACHED` | `409` duplicate registration number.

---

## `GET /api/v1/vehicles/{id}`
**Roles:** `admin`, `operator`, `dispatcher`

**Response `200`:** Single vehicle object.
**Errors:** `404` if not found or belongs to another tenant.

---

## `PATCH /api/v1/vehicles/{id}`
**Roles:** `admin`, `operator`

**Request** (all optional):
```json
{ "status": "maintenance", "fuel": 45, "routeId": "route-uuid", "driverId": null }
```
**Response `200`:** Updated vehicle object.

---

## `DELETE /api/v1/vehicles/{id}`
**Roles:** `admin`

Soft deletes the vehicle. Vehicle must not have `status: "active"`.

**Response `204`.**
**Errors:** `400` if vehicle is currently active.
