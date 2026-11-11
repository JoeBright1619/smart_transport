# API Spec — Service Integration

> **Base path:** `/api/v1/service`
> **Authentication:** Send a JWT as `Authorization: Bearer <token>` or a service token as `X-Service-Token: <token>`, according to the endpoint contract below.

These endpoints intentionally use two different authentication contracts.
`whoami` remains tenant-scoped so `gps_service` can discover its own tenant at
startup. The other endpoints are cross-tenant because `passenger_service` must
retrieve fleet, route, and arrival-sequence data without a tenant filter. Do
not assume that a credential accepted by one group is accepted by the other.

---

## Tenant-scoped: whoami

### `GET /api/v1/service/whoami`

**Purpose:** Lets `gps_service` discover the tenant associated with its own
credential at startup.

**Auth:** Either of the following:

- A **tenant-bound** service token with the `vehicles:read` scope, sent in
  `X-Service-Token`.
- An `admin`, `operator`, or `dispatcher` JWT, sent as a Bearer token.

Universal service tokens are rejected here because they have no tenant to
identify. Superadmin JWTs are also not accepted by this endpoint.

**Query params:** None.

**Response `200`:**

```json
{
  "data": {
    "tenant_id": "ten-demo-001",
    "tenant_name": "EcoFleet Rwanda"
  },
  "meta": null,
  "error": null
}
```

**Errors:**

- `401 UNAUTHORIZED` — missing, invalid, or inactive credential.
- `403 FORBIDDEN` — service token lacks `vehicles:read`, token tenant is
  inactive, or JWT role is not admin/operator/dispatcher.

---

## Cross-tenant endpoints

These endpoints ignore `tenant_id` and can return active records for any
tenant. They are for `passenger_service` integration, including fleet refresh,
route lookups, and arrival-sequence recovery.

**Auth for every endpoint in this section:**

- A superadmin JWT; or
- A **universal** service token (`tenant_id` is `NULL`) with
  `vehicles:read_universal`, sent in `X-Service-Token`.

Tenant-bound service tokens are rejected here, even if they have a similarly
named scope. This prevents a tenant credential from being treated as
cross-tenant access.

### `GET /api/v1/service/routes/{id}`

**Path params:** `id` — route ID.

**Query params:** None.

**Response `200`:** Standard API envelope containing a route with `id`,
`name`, `number`, `distance`, `duration`, `color`, `isActive`, `createdAt`, and
its ordered `stops` (`id`, `name`, `lat`, `lng`, `order`).

**Errors:**

- `401 UNAUTHORIZED` — missing, invalid, or inactive credential.
- `403 FORBIDDEN` — non-superadmin JWT, missing scope, or tenant-bound token.
- `404 route_not_found` — no non-deleted route exists with that ID.

### `GET /api/v1/service/vehicles`

**Query params:**

- `status` (optional) — active-vehicle status filter.
- `page` (default `1`, minimum `1`).
- `page_size` (default `20`, minimum `1`, maximum `100`).

**Response `200`:** Paginated standard envelope. Each vehicle includes `id`,
`tenantId`, `registrationNumber`, `model`, `seatingCapacity`,
`currentOccupancy`, `status`, `currentLocation`, `speed`, `heading`, `fuel`,
`engineStatus`, `routeId`, `driverId`, `plannedLoops`, `completedLoops`,
`lastUpdate`, and `remainingSeats`. `meta` contains `total`, `page`, and
`pageSize`.

**Errors:**

- `401 UNAUTHORIZED` — missing, invalid, or inactive credential.
- `403 FORBIDDEN` — non-superadmin JWT, missing scope, or tenant-bound token.
- `422 VALIDATION_ERROR` — invalid pagination values.

### `GET /api/v1/service/vehicles/{id}`

**Path params:** `id` — vehicle ID.

**Query params:** None.

**Response `200`:** Standard API envelope containing the same vehicle shape
as the cross-tenant vehicle list.

**Errors:**

- `401 UNAUTHORIZED` — missing, invalid, or inactive credential.
- `403 FORBIDDEN` — non-superadmin JWT, missing scope, or tenant-bound token.
- `404 vehicle_not_found` — no non-deleted vehicle exists with that ID.

### `GET /api/v1/service/vehicles/{id}/latest-arrival-sequence`

**Path params:** `id` — vehicle ID.

**Query params:** None.

**Response `200`:**

```json
{
  "data": { "arrivalSequence": 42 },
  "meta": null,
  "error": null
}
```

`arrivalSequence` is the highest sequence recorded in `occupancy_events` for
the vehicle. `passenger_service` can use it when recovering its stop-arrival
state.

**Errors:**

- `401 UNAUTHORIZED` — missing, invalid, or inactive credential.
- `403 FORBIDDEN` — non-superadmin JWT, missing scope, or tenant-bound token.
- `404 vehicle_not_found` — no non-deleted vehicle exists with that ID.
- `404 no_arrival_records` — the vehicle exists but has no occupancy event.
