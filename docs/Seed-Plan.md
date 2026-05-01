# Database Seed Plan

> **Purpose:** Defines the exact initial state of the database for local development and testing.
> Run the seed script after running Alembic migrations on a fresh database.
> **File location:** `backend/app/core/seed.py`

---

## How to Run

```bash
# 1. Apply all migrations first
alembic upgrade head

# 2. Run the seed script
python -m app.core.seed
```

The seed script must be **idempotent** — running it twice must not create duplicates.
Use `INSERT ... ON CONFLICT DO NOTHING` or check for existence before inserting.

---

## 1. Superadmin Account

One superadmin is seeded directly — this cannot be created through any API endpoint.

| Field | Value |
|---|---|
| `id` | `user-superadmin-001` |
| `fullName` | `Platform Admin` |
| `email` | `superadmin@platform.local` |
| `password` | From env var `SUPERADMIN_PASSWORD` (default: `Admin@123456` for dev only) |
| `role` | `superadmin` |
| `tenantId` | `null` |

> ⚠️ Change `SUPERADMIN_PASSWORD` immediately in any non-local environment.

---

## 2. Demo Tenant

One company seeded for development and manual testing.

| Field | Value |
|---|---|
| `id` | `ten-demo-001` |
| `name` | `Kigali Express Ltd` |
| `contactEmail` | `admin@kigaliexpress.rw` |
| `isActive` | `true` |

---

## 3. Demo Users (all belong to `ten-demo-001`)

All demo users share password: `Password123!` (dev only — set via `SEED_PASSWORD` env var)

| id | fullName | email | role |
|---|---|---|---|
| `user-admin-001` | `Jean Claude Mugabo` | `admin@kigaliexpress.rw` | `admin` |
| `user-operator-001` | `Marie Umutesi` | `operator@kigaliexpress.rw` | `operator` |
| `user-dispatcher-001` | `Eric Nsabimana` | `dispatcher@kigaliexpress.rw` | `dispatcher` |
| `user-passenger-001` | `Alice Uwera` | `passenger@kigaliexpress.rw` | `passenger` |

---

## 4. Demo Routes (all belong to `ten-demo-001`)

### Route 1 — Nyabugogo ↔ Kimironko
| Field | Value |
|---|---|
| `id` | `route-001` |
| `name` | `Nyabugogo - Kimironko` |
| `number` | `101` |
| `distance` | `12.5` km |
| `duration` | `35` min |
| `color` | `#3B82F6` |
| `isActive` | `true` |

**Stops:**
| order | name | lat | lng |
|---|---|---|---|
| 1 | Nyabugogo | -1.9396 | 30.0585 |
| 2 | Kacyiru | -1.9453 | 30.0907 |
| 3 | Remera | -1.9553 | 30.1127 |
| 4 | Kimironko | -1.9441 | 30.1341 |

### Route 2 — CBD ↔ Gisozi
| Field | Value |
|---|---|
| `id` | `route-002` |
| `name` | `CBD - Gisozi` |
| `number` | `202` |
| `color` | `#10B981` |
| `isActive` | `true` |

**Stops:**
| order | name | lat | lng |
|---|---|---|---|
| 1 | CBD (City Hall) | -1.9500 | 30.0588 |
| 2 | Muhima | -1.9520 | 30.0481 |
| 3 | Gisozi | -1.9317 | 30.0521 |

---

## 5. Demo Drivers (all belong to `ten-demo-001`)

| id | name | licenseNumber | status | certificationExpiry |
|---|---|---|---|---|
| `drv-001` | `Patrick Hakizimana` | `DL-RW-0001` | `available` | `2027-06-30` |
| `drv-002` | `Solange Uwimana` | `DL-RW-0002` | `available` | `2027-09-15` |
| `drv-003` | `Claude Niyomugabo` | `DL-RW-0003` | `off-duty` | `2026-12-01` |

---

## 6. Demo Vehicles (all belong to `ten-demo-001`)

| id | registration | model | capacity | status | route | driver |
|---|---|---|---|---|---|---|
| `veh-001` | `RAD 001 A` | `Yutong ZK6120` | 60 | `active` | `route-001` | `drv-001` |
| `veh-002` | `RAD 002 B` | `King Long XMQ` | 45 | `idle` | `null` | `null` |
| `veh-003` | `RAD 003 C` | `Yutong ZK6120` | 60 | `active` | `route-002` | `drv-002` |
| `veh-004` | `RAD 004 D` | `Higer KLQ` | 30 | `maintenance` | `null` | `null` |

Seed each vehicle with an initial position near the start of their route:
- `veh-001`: `lat: -1.9396, lng: 30.0585, speed: 35, heading: 90, fuel: 80`
- `veh-003`: `lat: -1.9500, lng: 30.0588, speed: 28, heading: 0, fuel: 62`

---

## 7. Demo Maintenance Records

| vehicleId | type | description | status | scheduledDate |
|---|---|---|---|---|
| `veh-004` | `repair` | `Engine oil leak repair` | `in-progress` | `2026-04-05` |
| `veh-001` | `routine` | `Tyre rotation and inspection` | `scheduled` | `2026-04-20` |

---

## 8. Demo Alerts (pre-seeded for UI testing)

| type | severity | vehicleId | title | isAcknowledged |
|---|---|---|---|---|
| `maintenance` | `medium` | `veh-004` | `Maintenance Due: RAD 004 D` | `false` |
| `speeding` | `high` | `veh-001` | `Speeding Detected: RAD 001 A` | `false` |
| `delay` | `low` | `veh-003` | `Trip Delay: RAD 003 C` | `true` |

---

## 9. Additional Env Variables for Seed Script

Add to `.env.example`:
```env
SUPERADMIN_PASSWORD=Admin@123456
SEED_PASSWORD=Password123!
RUN_SEED=true
```

Set `RUN_SEED=false` in staging/production to prevent accidental re-seeding.
