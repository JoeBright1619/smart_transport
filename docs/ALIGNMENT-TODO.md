# Documentation Alignment TODO

Tracks all tasks needed to reconcile `shared/guidelines/entities.md` with the UML class diagram and propagate consistent decisions across all project docs.

Work top-to-bottom — items marked **DECISION REQUIRED** must be resolved before dependent tasks can be executed.

---

## Group 1 — Architecture Decisions ✅ RESOLVED

All three decisions are resolved from the codebase. Recorded in `shared/guidelines/conventions.md`.

- [x] **ID strategy → UUID v4 strings with entity prefixes**
  - Confirmed in ORM models (`user-<uuid>`, `veh-<uuid>`, `drv-<uuid>`, etc.)
  - Class diagram needs updating: replace all `Long` with `String (UUID)`

- [x] **User modeling → flat `role` enum**
  - Confirmed in `models/user.py`: single `User` table with `role` Enum column
  - Class diagram needs updating: remove `Administrator`/`FleetOperator`/`Dispatcher` subclasses, add `role` field

- [x] **Telemetry → separate `Telemetry` entity (append-only log)**
  - Decision: dedicated table for historical GPS records; `Vehicle` keeps current snapshot fields for fast live reads
  - `entities.md` updated with `Telemetry` entity and rules
  - `docs/api/tracking.md` updated with persistence contract
  - Backend: new ORM model + migration required (see `IMPLEMENTATION.md` tasks 2.11/2.12)

---

## Group 2 — `entities.md` Updates

Update `shared/guidelines/entities.md` after Group 1 decisions are made.

- [x] **Add `Telemetry` entity** ✅
  - Added to `entities.md` entity table and documented in a dedicated Telemetry section with field rules and append-only constraint

- [x] **Document `passwordHash` handling** ✅
  - Confirmed in `models/user.py`: `password_hash` column lives directly on the `User` table
  - `entities.md` `User` row updated to include `passwordHash`

- [x] **Add `isDeleted` to entity table** ✅
  - `entities.md` `User` row updated to include `isDeleted`
  - Soft Delete section updated with explicit list of which entities carry `isDeleted` and which are exceptions

---

## Group 3 — Class Diagram Updates

Update the PlantUML source after Group 1 decisions are made. One pass should cover all items below.

- [ ] **Add `Tenant` class and `tenantId` to all entities**
  - `Tenant`: `id`, `name`, `contactEmail`, `isActive`
  - Add `tenantId` field to: `User`, `Vehicle`, `Driver`, `Route`, `Stop`, `Trip`, `MaintenanceRecord`, `Alert`
  - Add association: `Tenant "1" -- "0..*" User` (and similarly for other entities, or use a note)

- [ ] **Update `User` to flat role model** *(if that decision is taken)*
  - Remove `Administrator`, `FleetOperator`, `Dispatcher` subclasses
  - Add `role: String` field to `User` with enum values noted
  - Add `phone: String` field (present in `entities.md`, missing from class diagram)
  - Remove `isActive` from `User` (in `entities.md` `isActive` lives on `Tenant`, not `User`)

- [ ] **Update `Vehicle` fields**
  - Replace `fuelType: String` → `fuel: Int` (percentage 0–100) + `engineStatus: String` (`good|warning|critical`)
  - Add `model: String`
  - Add `currentLocation: Location` (or `lat/lng` if keeping flat fields)
  - Add `heading: Int`, `routeId`, `driverId`

- [ ] **Update `Driver` fields**
  - Add `rating: Double`, `totalTrips: Int`, `status: String` (`available|on-trip|off-duty`), `certificationExpiry: Date`

- [ ] **Update `Trip` fields**
  - Add `scheduledEnd: DateTime`, `actualEnd: DateTime`
  - Add `passengers: Int`, `delay: Int`
  - Rename `scheduledStartTime` → `scheduledStart` and `actualStartTime` → `actualStart` (match `entities.md` naming)

- [ ] **Update `MaintenanceRecord` fields**
  - Replace `serviceDate: Date` → `scheduledDate: Date` + `completedDate: Date`
  - Add `type: String` (`routine|repair|inspection`), `status: String` (`scheduled|in-progress|completed`), `nextDue: Date`
  - Add explicit `vehicleId` reference field

- [ ] **Update `Alert` fields**
  - Rename `isResolved: Boolean` → `isAcknowledged: Boolean`
  - Add `title: String`, `timestamp: DateTime`
  - Add optional `driverId` association (Alert can target a Driver, not only a Vehicle)

- [x] **Update `Stop` location format** ✅ — confirmed flat `lat`/`lng` columns from codebase (`models/route.py`, `models/vehicle.py`); class diagram needs updating to match

- [ ] **Update `Route` fields**
  - Add `number: String`, `color: String`, `isActive: Boolean`
  - Rename `distanceKm` → `distance` and `estimatedDurationMin` → `duration` (match `entities.md`)

- [ ] **Add `Analytics` class**
  - Fields: `tenantId`, `date`, `totalTrips`, `onTimePercentage`, `avgDelay`, `totalPassengers`, `fuelConsumption`, `revenue`
  - Association: `Tenant "1" -- "0..*" Analytics`

- [ ] **Add `AuditLog` class**
  - Fields: `id`, `tenantId`, `userId`, `entityType`, `entityId`, `actionType`, `metadata`, `createdAt`
  - Association: `User "1" -- "0..*" AuditLog`
  - Remove `viewAuditLogs()` method from `Administrator` (behavior belongs in the app layer, not the model)

- [ ] **Add soft delete annotation**
  - Add `isDeleted: Boolean` field to all operational entities in the diagram
  - Or add a diagram note: "All operational entities carry `isDeleted: Boolean`, defaulting to false"

---

## Group 4 — Propagation to Other Docs

Once Groups 1–3 are resolved, verify these docs are consistent with the final entity shapes.

- [ ] **`docs/api/` — check all endpoint docs**
  - `auth.md` — verify User fields match final User entity (role enum, passwordHash handling)
  - `vehicles.md` — verify request/response shapes match updated Vehicle fields
  - `drivers.md` — verify Driver fields (rating, totalTrips, certificationExpiry)
  - `trips.md` — verify Trip fields (scheduledEnd, actualEnd, delay)
  - `tracking.md` — verify this aligns with the Telemetry decision
  - `analytics.md` — verify Analytics entity fields match

- [ ] **`shared/guidelines/multi-tenancy.md`** — confirm `Tenant` entity definition here matches `entities.md` after any Tenant field changes

- [ ] **`shared/guidelines/api-contracts.md`** — verify ID format rules reflect the ID strategy decision

- [ ] **`docs/Architecture.md`** — check if the user role model section reflects the final flat vs inheritance decision

- [ ] **`frontend/lib/types.ts`** *(code, not doc)* — after entities.md is finalized, verify TypeScript types match. `entities.md` itself mandates this propagation.

- [ ] **Backend ORM models + Pydantic schemas** *(code, not doc)* — same propagation requirement as above.

---

## Completion Checklist

- [ ] All Group 1 decisions recorded in `shared/guidelines/conventions.md`
- [ ] `entities.md` updated and self-consistent
- [ ] Class diagram PlantUML source updated and re-exported
- [ ] All `docs/api/` endpoint docs verified
- [ ] `frontend/lib/types.ts` matches final entities
- [ ] Backend schemas match final entities
