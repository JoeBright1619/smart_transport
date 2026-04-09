# API Spec — Drivers

> **Roles:** `admin`, `operator` for write. `dispatcher` read-only.

---

## `GET /api/v1/drivers`
**Roles:** `admin`, `operator`, `dispatcher`
**Query params:** `?status=available&page=1&page_size=20`

**Response `200`:**
```json
{
  "data": [
    {
      "id": "drv-uuid",
      "name": "Patrick Hakizimana",
      "licenseNumber": "DL-RW-0001",
      "phone": "+250788111222",
      "rating": 4.7,
      "totalTrips": 143,
      "status": "available",
      "vehicleId": null,
      "certificationExpiry": "2027-06-30",
      "createdAt": "2026-04-01T08:00:00Z"
    }
  ],
  "meta": { "total": 3, "page": 1, "pageSize": 20 }
}
```

---

## `POST /api/v1/drivers`
**Roles:** `admin`, `operator`

**Request:**
```json
{
  "name": "Eric Nsabimana",
  "licenseNumber": "DL-RW-0003",
  "phone": "+250788345678",
  "certificationExpiry": "2027-12-31"
}
```
**Response `201`:** Driver object with `status: "available"` and `rating: 0`, `totalTrips: 0`.
**Errors:** `409` duplicate licence number.

---

## `GET /api/v1/drivers/{id}`
**Roles:** `admin`, `operator`, `dispatcher`

**Response `200`:** Single driver object including `vehicleId` if currently assigned.
**Errors:** `404` if not found or belongs to another tenant.

---

## `PATCH /api/v1/drivers/{id}`
**Roles:** `admin`, `operator`

**Request** (all optional):
```json
{ "phone": "+250788999000", "status": "off-duty", "certificationExpiry": "2028-01-01" }
```
> `vehicleId` can be set to assign or unassign a vehicle. Cannot change `status` to `on-trip` manually — trips manage this automatically.

**Response `200`:** Updated driver object.

---

## `DELETE /api/v1/drivers/{id}`
**Roles:** `admin`

Soft deletes the driver.

**Response `204`.**
**Errors:** `400` if driver has `status: "on-trip"`.
