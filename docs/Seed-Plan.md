# Database Seed Plan

> **Purpose:** Defines the exact initial state of the database for development and demo purposes.
> Run the seed script after applying Alembic migrations on a fresh database.
> **File location:** `backend/app/core/seed.py`

---

## How to Run

Always run the seed inside the Docker container so it connects to the correct database:

```bash
# 1. Start services
docker compose up -d

# 2. Apply all migrations
docker compose exec backend alembic upgrade head

# 3. Run the seed script
docker compose exec backend python -m app.core.seed
```

> **Warning:** Do not run `python -m app.core.seed` directly from your local terminal. It will connect to your local PostgreSQL (if any) instead of the Docker database and the data will not appear in the app.

The seed script is **idempotent** — running it twice will not create duplicates. Every section checks for existence before inserting.

---

## 1. Superadmin Account

One superadmin is seeded directly — it cannot be created through any API endpoint.

| Field | Value |
|---|---|
| `id` | `user-superadmin-001` |
| `fullName` | `Platform Admin` |
| `email` | `superadmin@platform.local` |
| `password` | `Admin@123456` (override with `SUPERADMIN_PASSWORD` env var) |
| `role` | `superadmin` |
| `tenantId` | `null` |

> Change `SUPERADMIN_PASSWORD` immediately in any non-local environment.

---

## 2. Demo Tenant

| Field | Value |
|---|---|
| `id` | `ten-demo-001` |
| `name` | `EcoFleet Ltd` |
| `contactEmail` | `admin@ecofleet.rw` |
| `isActive` | `true` |

---

## 3. Demo Users (all belong to `ten-demo-001`)

All demo users share password: `Password123!` (override with `SEED_PASSWORD` env var)

| id | fullName | email | role |
|---|---|---|---|
| `user-admin-001` | `Jean Claude Mugabo` | `admin@ecofleet.rw` | `admin` |
| `user-operator-001` | `Marie Umutesi` | `operator@ecofleet.rw` | `operator` |
| `user-dispatcher-001` | `Eric Nsabimana` | `dispatcher@ecofleet.rw` | `dispatcher` |
| `user-passenger-001` | `Alice Uwera` | `passenger@ecofleet.rw` | `passenger` |

---

## 4. Demo Routes (all belong to `ten-demo-001`)

### Route 1 — Nyabugogo - Kimironko

| Field | Value |
|---|---|
| `id` | `route-001` |
| `number` | `101` |
| `distance` | `12.5 km` |
| `duration` | `35 min` |
| `color` | `#3B82F6` |

**Stops:**

| order | name | lat | lng |
|---|---|---|---|
| 1 | Nyabugogo | -1.9396 | 30.0585 |
| 2 | Kacyiru | -1.9453 | 30.0907 |
| 3 | Remera | -1.9553 | 30.1127 |
| 4 | Kimironko | -1.9441 | 30.1341 |

### Route 2 — CBD - Gisozi

| Field | Value |
|---|---|
| `id` | `route-002` |
| `number` | `202` |
| `distance` | `8.0 km` |
| `duration` | `25 min` |
| `color` | `#10B981` |

**Stops:**

| order | name | lat | lng |
|---|---|---|---|
| 1 | CBD (City Hall) | -1.9500 | 30.0588 |
| 2 | Muhima | -1.9520 | 30.0481 |
| 3 | Gisozi | -1.9317 | 30.0521 |

### Route 3 — Remera - Kanombe

| Field | Value |
|---|---|
| `id` | `route-003` |
| `number` | `303` |
| `distance` | `10.2 km` |
| `duration` | `30 min` |
| `color` | `#F59E0B` |

**Stops:**

| order | name | lat | lng |
|---|---|---|---|
| 1 | Remera | -1.9553 | 30.1127 |
| 2 | Masaka | -1.9721 | 30.1312 |
| 3 | Nyanza | -1.9745 | 30.1389 |
| 4 | Kanombe Airport | -1.9688 | 30.1398 |

### Route 4 — Kicukiro - Nyabugogo

| Field | Value |
|---|---|
| `id` | `route-004` |
| `number` | `404` |
| `distance` | `9.5 km` |
| `duration` | `28 min` |
| `color` | `#8B5CF6` |

**Stops:**

| order | name | lat | lng |
|---|---|---|---|
| 1 | Kicukiro | -1.9742 | 30.0904 |
| 2 | Niboye | -1.9661 | 30.0785 |
| 3 | Gitega | -1.9596 | 30.0631 |
| 4 | Nyabugogo | -1.9396 | 30.0585 |

### Route 5 — Gikondo - Kimironko

| Field | Value |
|---|---|
| `id` | `route-005` |
| `number` | `505` |
| `distance` | `14.0 km` |
| `duration` | `40 min` |
| `color` | `#EF4444` |

**Stops:**

| order | name | lat | lng |
|---|---|---|---|
| 1 | Gikondo | -1.9726 | 30.0642 |
| 2 | Sonatubes | -1.9636 | 30.0795 |
| 3 | Remera | -1.9553 | 30.1127 |
| 4 | Biryogo | -1.9502 | 30.1140 |
| 5 | Kimironko | -1.9441 | 30.1341 |

---

## 5. Demo Drivers (all belong to `ten-demo-001`)

| id | name | licenseNumber | phone | status | certificationExpiry |
|---|---|---|---|---|---|
| `drv-001` | `Patrick Hakizimana` | `DL-RW-0001` | `+250700000001` | `available` | `2027-06-30` |
| `drv-002` | `Solange Uwimana` | `DL-RW-0002` | `+250700000002` | `available` | `2027-09-15` |
| `drv-003` | `Claude Niyomugabo` | `DL-RW-0003` | `+250700000003` | `off-duty` | `2026-12-01` |
| `drv-004` | `Josephine Mukandori` | `DL-RW-0004` | `+250700000004` | `available` | `2027-03-20` |
| `drv-005` | `Emmanuel Ntwali` | `DL-RW-0005` | `+250700000005` | `available` | `2027-07-10` |
| `drv-006` | `Diane Ingabire` | `DL-RW-0006` | `+250700000006` | `available` | `2027-11-05` |
| `drv-007` | `Jean Baptiste Rutaganda` | `DL-RW-0007` | `+250700000007` | `available` | `2028-01-15` |
| `drv-008` | `Grace Uwamahoro` | `DL-RW-0008` | `+250700000008` | `off-duty` | `2027-04-22` |

---

## 6. Demo Vehicles (all belong to `ten-demo-001`)

| id | registration | model | capacity | status | route | driver | lat | lng | speed | heading | fuel |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `veh-001` | `RAD 001 A` | `Yutong ZK6120` | 60 | `active` | `route-001` | `drv-001` | -1.9396 | 30.0585 | 35 | 90 | 80 |
| `veh-002` | `RAD 002 B` | `King Long XMQ` | 45 | `idle` | — | — | — | — | — | — | 100 |
| `veh-003` | `RAD 003 C` | `Yutong ZK6120` | 60 | `active` | `route-002` | `drv-002` | -1.9500 | 30.0588 | 28 | 0 | 62 |
| `veh-004` | `RAD 004 D` | `Higer KLQ` | 30 | `maintenance` | — | — | — | — | — | — | 100 |
| `veh-005` | `RAD 005 E` | `Yutong ZK6120` | 60 | `idle` | — | — | — | — | — | — | 95 |
| `veh-006` | `RAD 006 F` | `King Long XMQ` | 45 | `active` | `route-003` | `drv-004` | -1.9553 | 30.1127 | 30 | 180 | 74 |
| `veh-007` | `RAD 007 G` | `Higer KLQ` | 40 | `active` | `route-004` | `drv-005` | -1.9742 | 30.0904 | 25 | 45 | 58 |
| `veh-008` | `RAD 008 H` | `Yutong ZK6120` | 60 | `active` | `route-005` | `drv-006` | -1.9726 | 30.0642 | 32 | 270 | 67 |

Active vehicles (veh-001, 003, 006, 007, 008) are seeded with initial lat/lng so they appear on the live tracking map immediately.

---

## 7. Demo Maintenance Records

| vehicleId | type | description | status | scheduledDate | cost (RWF) |
|---|---|---|---|---|---|
| `veh-004` | `repair` | `Engine oil leak repair` | `in-progress` | `2026-04-05` | 45,000 |
| `veh-001` | `routine` | `Tyre rotation and inspection` | `scheduled` | `2026-04-20` | 0 |
| `veh-002` | `inspection` | `Annual roadworthiness inspection` | `completed` | `2026-03-10` | 18,000 |
| `veh-003` | `routine` | `Engine oil and filter change` | `completed` | `2026-03-22` | 12,500 |
| `veh-005` | `repair` | `Brake pad replacement - front axle` | `completed` | `2026-04-01` | 35,000 |
| `veh-006` | `routine` | `Air filter and coolant service` | `scheduled` | `2026-05-15` | 0 |
| `veh-007` | `inspection` | `Transmission fluid check` | `scheduled` | `2026-05-28` | 0 |
| `veh-008` | `repair` | `Side mirror replacement` | `completed` | `2026-04-12` | 8,500 |

---

## 8. Demo Alerts

| type | severity | vehicleId | driverId | title | isAcknowledged |
|---|---|---|---|---|---|
| `maintenance` | `medium` | `veh-004` | — | `Maintenance Due: RAD 004 D` | `false` |
| `speeding` | `high` | `veh-001` | `drv-001` | `Speeding Detected: RAD 001 A` | `false` |
| `delay` | `low` | `veh-003` | `drv-002` | `Trip Delay: RAD 003 C` | `true` |
| `breakdown` | `critical` | `veh-004` | — | `Breakdown: RAD 004 D` | `false` |
| `geofence` | `medium` | `veh-006` | `drv-004` | `Geofence Alert: RAD 006 F` | `true` |
| `speeding` | `high` | `veh-008` | `drv-006` | `Speeding Detected: RAD 008 H` | `false` |
| `delay` | `medium` | `veh-007` | `drv-005` | `Trip Delay: RAD 007 G` | `false` |
| `info` | `low` | — | — | `System: Seed Data Loaded` | `true` |

---

## 9. Historical Trips (90-day backfill)

5 active vehicle/route/driver assignments, 2 departures per day (07:00 and 13:30), 90 days = **~900 trip records**.

| vehicleId | routeId | driverId | routeDuration |
|---|---|---|---|
| `veh-001` | `route-001` | `drv-001` | 35 min |
| `veh-003` | `route-002` | `drv-002` | 25 min |
| `veh-006` | `route-003` | `drv-004` | 30 min |
| `veh-007` | `route-004` | `drv-005` | 28 min |
| `veh-008` | `route-005` | `drv-006` | 40 min |

Per trip:
- 82% on-time rate; delays drawn from `randint(5, 18)` minutes when late
- Passengers: `randint(28, 55)` per trip
- All trips seeded with `status = "completed"` and a historical `created_at` timestamp

The seed skips this section if 100 or more historical trips already exist for the tenant.

---

## 10. Analytics Records (90-day backfill)

One `AnalyticsRecord` row per day for the past 90 days.

| field | derivation |
|---|---|
| `date` | Each calendar day in the 90-day window |
| `totalFuelConsumption` | Sum of `uniform(22, 35)` L per active vehicle (~135 L/day average) |
| `totalRevenue` | `daily_passengers × 300 RWF × uniform(0.90, 1.10)` (~120,000 RWF/day average) |

Each day uses a deterministic seed (`random.seed(day.toordinal())`) so re-running produces the same values.

The seed skips this section if 30 or more analytics records already exist for the tenant.

---

## 11. Environment Variables for Seed Script

Add to `backend/.env.example`:

```env
SUPERADMIN_PASSWORD=Admin@123456
SEED_PASSWORD=Password123!
```

Set strong values for both in any non-local environment.
