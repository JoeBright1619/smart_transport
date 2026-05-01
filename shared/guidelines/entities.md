# Shared — Domain Entity Definitions

> **Canonical source of truth for all data models.**
> Any change to an entity shape must be made here first, then propagated to the frontend `lib/types.ts` and the backend ORM model + Pydantic schema.

---

## Multi-Tenancy Requirement

All operational entities MUST include a `tenantId` field linking them to a specific transport company. Data from one tenant must **never** be accessible to another. Enforcement rules are in [`multi-tenancy.md`](./multi-tenancy.md).

---

## Entity Definitions

| Entity | Key Fields |
|---|---|
| `Tenant` | `id`, `name`, `contactEmail`, `isActive`, `createdAt`, `updatedAt` |
| `User` | `id`, `tenantId`, `email`, `fullName`, `role` (`superadmin\|admin\|operator\|dispatcher\|passenger`), `phone` |
| `Vehicle` | `id`, `tenantId`, `registrationNumber`, `model`, `capacity`, `status` (`active\|idle\|maintenance\|offline`), `currentLocation {lat, lng}`, `speed`, `heading`, `routeId`, `driverId`, `fuel`, `engineStatus` (`good\|warning\|critical`) |
| `Route` | `id`, `tenantId`, `name`, `number`, `stops[]`, `distance`, `duration`, `isActive`, `color` |
| `Stop` | `id`, `tenantId`, `name`, `location {lat, lng}`, `order` |
| `Trip` | `id`, `tenantId`, `vehicleId`, `routeId`, `driverId`, `scheduledStart`, `actualStart`, `scheduledEnd`, `actualEnd`, `status` (`scheduled\|active\|completed\|cancelled`), `passengers`, `delay` |
| `Driver` | `id`, `tenantId`, `name`, `licenseNumber`, `phone`, `rating`, `totalTrips`, `status` (`available\|on-trip\|off-duty`), `vehicleId`, `certificationExpiry` |
| `MaintenanceRecord` | `id`, `tenantId`, `vehicleId`, `type` (`routine\|repair\|inspection`), `description`, `scheduledDate`, `completedDate`, `cost`, `status` (`scheduled\|in-progress\|completed`), `nextDue` |
| `Alert` | `id`, `tenantId`, `type` (`delay\|breakdown\|maintenance\|geofence\|speeding\|info`), `severity` (`low\|medium\|high\|critical`), `title`, `message`, `vehicleId?`, `driverId?`, `timestamp`, `isAcknowledged` |
| `Analytics` | `tenantId`, `date`, `totalTrips`, `onTimePercentage`, `avgDelay`, `totalPassengers`, `fuelConsumption`, `revenue` |
| `AuditLog` | `id`, `tenantId`, `userId`, `entityType`, `entityId`, `actionType` (`create\|update\|soft_delete\|login\|impersonate`), `metadata` (JSON diff), `createdAt` |

---

## Field Rules

- **IDs** — Always UUID v4 strings, prefixed by entity type: `veh-`, `drv-`, `route-`, `trip-`, `ten-`
- **Timestamps** — Always ISO 8601 UTC strings: `2026-03-24T12:00:00Z`. Field names use `camelCase` + `At` suffix: `createdAt`, `updatedAt`, `completedAt`
- **Booleans** — `is` or `has` prefix: `isActive`, `isAcknowledged`, `isDeleted`
- **Status enums** — Always lowercase strings: `'active'`, `'on-trip'`, `'in-progress'`
- **Location** — `{ lat: number, lng: number }` decimal degrees, WGS84 coordinate system
- **Speed** — km/h (integer).
- **Distance** — km (decimal).
- **Fuel** — percentage 0–100.
- **Delay** — minutes (integer).
- **Heading** — degrees 0–360 clockwise from north

---

## Soft Delete

All operational entities have an `isDeleted` (`is_deleted` in DB) boolean field defaulting to `false`. Records are never physically deleted — they are soft-deleted. All list queries must filter `WHERE is_deleted = FALSE`.

Exceptions: `AuditLog` (immutable, never deleted), `Tenant` (deactivated via `isActive`, not deleted).
