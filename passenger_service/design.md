# Passenger Service — Design Document

## 1. Architecture Diagram

```text
                     ┌──────────────┐
                     │  backend DB  │
                     │  (PostgreSQL)│
                     └───┬─────┬───┘
                         │     │
                    HTTP │     │ HTTP
          (vehicles,     │     │  (routes,
           whoami)       │     │   stops,
                         │     │   whoami)
                   ┌─────▼──┐  │
                   │  gps_   │  │
                   │ service │  │
                   └────┬────┘  │
                        │       │
        MQTT publish    │       │
  gps/{t}/{v}/position  │       │
                        │       │
              ┌─────────▼───────▼────────┐
              │    passenger_service     │
              │                          │
              │  ┌─────────────────────┐ │
              │  │ MQTT subscriber     │ │
              │  │ (position events)   │ │
              │  └─────────┬───────────┘ │
              │            │             │
              │  ┌─────────▼───────────┐ │
              │  │ stop-arrival        │ │
              │  │ detector            │ │
              │  └─────────┬───────────┘ │
              │            │             │
              │  ┌─────────▼───────────┐ │
              │  │ passenger           │ │
              │  │ simulator           │ │
              │  └─────────┬───────────┘ │
              │            │             │
              │  ┌─────────▼───────────┐ │
              │  │ MQTT publisher      │ │
              │  │ (occupancy events)  │ │
              │  └─────────┬───────────┘ │
              │            │             │
              │  ┌─────────────────────┐ │
              │  │ route_cache (HTTP)  │ │
              │  └─────────────────────┘ │
              │  ┌─────────────────────┐ │
              │  │ FastAPI (health/    │ │
              │  │ status only)        │ │
              │  └─────────────────────┘ │
              └────────────┬─────────────┘
                           │
           MQTT publish    │
   gps/{t}/{v}/occupancy   │
                           │
              ┌────────────▼─────────────┐
              │   backend subscriber     │
              │   (occupancy events)     │
              │   → boarding_records     │
              │   → vehicles.             │
              │      current_occupancy   │
              │   → capacity alerts      │
              │   → WebSocket broadcast  │
              └──────────────────────────┘
```

### Message flows

| # | From | To | Transport | Payload |
|---|------|----|-----------|---------|
| 1 | backend DB | gps_service | HTTP (`/api/v1/vehicles`, `/api/v1/service/whoami`) | Vehicle list, tenant identity |
| 2 | backend DB | gps_service | HTTP (`/api/v1/routes/{id}`) | Route stops |
| 3 | gps_service | MQTT broker | MQTT publish `gps/{tenant}/{vehicle}/position` | `GPSPositionUpdate` payload |
| 4 | MQTT broker | backend | MQTT subscribe `gps/+/+/position` | same |
| 5 | MQTT broker | passenger_service | MQTT subscribe `gps/+/+/position` | same |
| 6 | backend DB | passenger_service | HTTP (`/api/v1/routes/{id}`, `/api/v1/service/whoami`) | Route stops, tenant identity |
| 7 | passenger_service | MQTT broker | MQTT publish `gps/{tenant}/{vehicle}/occupancy` | `OccupancyEvent` payload |
| 8 | MQTT broker | backend | MQTT subscribe `gps/+/+/occupancy` | same |

### Latency and consistency

**Expected end-to-end lag for occupancy events:** ~5–15 seconds from the
physical event (bus at stop) to the backend DB commit. Composition:

| Stage | Typical | Notes |
|---|---|---|
| gps_service tick interval | up to `POLL_INTERVAL` (default 5s) | The simulator publishes once per tick; a bus arriving just after a tick waits one full interval. |
| MQTT publish → passenger_service receive | <100ms | Same broker, QoS 1. |
| Detection + simulation | <50ms | Pure calculation, plus one cached route lookup. |
| MQTT publish → backend receive | <100ms | Same broker, QoS 1. |
| Validation + DB transaction | <50ms | Two writes, single transaction. |

**Guarantees:**

- **At-least-once delivery** end to end (MQTT QoS 1 on both hops). Duplicates
  are possible; the idempotency key makes ingestion idempotent.
- **Per-vehicle ordering** is preserved. MQTT QoS 1 does not guarantee global
  ordering across topics, but events for a given vehicle arrive on the same
  topic and are processed in the order published.
- **No cross-vehicle ordering guarantee.** Events from different vehicles may
  be interleaved arbitrarily.

**Best-effort, not guaranteed:**

- **Correlation between position and occupancy timestamps.** The occupancy
  event carries the triggering position's timestamp, so the two streams can
  be joined chronologically — but the *arrival* of the two events at the
  backend is not synchronized. A frontend reading both topics may briefly
  display an occupancy event before the position it was derived from.

**Not handled in v1:**

- **Backpressure.** If the backend falls behind, MQTT QoS 1 buffers in the
  broker. At demo scale this never occurs; at scale, add a dead-letter
  queue and a slow-consumer alarm.
- **Clock skew between services.** All timestamps are UTC. If gps_service's
  clock drifts from passenger_service's, `service_timestamp −
  position_timestamp` may be misleading, but never negative for correctly
  ordered events. Assumes NTP-synced hosts.

---

## 2. Topic Layout Decision

### Decision: Keep the existing `gps/` prefix

**Current topic:** `gps/{tenant_id}/{vehicle_id}/position`

**New topic:** `gps/{tenant_id}/{vehicle_id}/occupancy`

### Justification

1. **Backwards compatibility.** Migrating to `tenant/{t}/vehicle/{v}/...` would require changes in:
   - `gps_service/simulator/orchestrator.py` (line 136–137, topic construction)
   - `gps_service/mqtt/payload.py` (docstring reference)
   - `gps_service/tests/test_orchestrator.py` (lines 123, 356 — topic assertions)
   - `backend/app/services/gps_mqtt_subscriber.py` (line 15, `GPS_POSITION_TOPIC` constant)
   - `backend/tests/test_gps_mqtt_subscriber.py`
   - `docker-compose.yml` (env vars referencing topics, if any)
   - Any Mosquitto ACL configuration

   This is a non-trivial migration that must be coordinated across two deployed services and the backend. It adds risk for no functional benefit at this stage.

2. **Semantic coherence.** The `gps/` prefix logically groups vehicle telemetry topics — both position and occupancy are vehicle telemetry triggered by GPS-based detection. Adding `/occupancy` under the same namespace keeps related data discoverable.

3. **Consistent with MQTT conventions.** MQTT topic hierarchies commonly group by data domain, not by service. The `gps/` prefix already functions as a domain prefix ("vehicle telemetry"), not a service-identity prefix.

4. **Future migration path.** If a cleaner hierarchy becomes necessary (e.g., when more event types are added or a third service publishes), that migration can be done as a dedicated task with proper versioning — not conflated with passenger_service delivery.

### Backend subscription

The backend currently subscribes to `gps/+/+/position`. It will add a second subscription: `gps/+/+/occupancy`. These are handled by separate callbacks so each can validate against its own schema.

---

## 3. Stop-Arrival Detection Algorithm

### What defines "at a stop"?

A vehicle is considered "at a stop" when **both** conditions are satisfied:

1. **Distance:** The vehicle's position is within `STOP_ARRIVAL_RADIUS_M = 30` metres of the stop's coordinates (haversine distance). This matches `STOP_ARRIVAL_THRESHOLD_METERS = 30` in `backend/app/services/route_tracking_service.py`.

2. **Speed:** The vehicle's reported speed is `<= STOP_SPEED_THRESHOLD_KMH = 5` km/h. This confirms the vehicle is actually stopping (not driving past at speed).

Either condition alone is insufficient:
- A vehicle at low speed far from any stop is in traffic, not at a stop.
- A vehicle within 30m but at 40 km/h is driving past (e.g., stops on both sides of a road).

### Debouncing

A **cooldown** mechanism prevents re-firing for the same stop:

- Per-vehicle state tracks `last_stop_id` and `last_arrival_ts`.
- A new arrival at the same `stop_id` is suppressed if fewer than `STOP_COOLDOWN_SECONDS = 60` seconds have elapsed since the previous arrival at that stop.
- This handles the case where a bus lingers near a stop (e.g., traffic light just past the stop, or backing up).
- Arrivals at *different* stops are never suppressed — a bus moving rapidly between closely-spaced stops correctly fires two events.

### How does the service know which route a vehicle is on?

Each incoming position message carries `vehicle_id` and `tenant_id`. The service maintains a **vehicle-to-route mapping** that it populates by:

1. **On startup:** Fetching active vehicles from `GET /api/v1/vehicles?status=active` (same endpoint as `VehicleFetcher`). Each vehicle record includes `route_id`.
2. **Periodically:** Re-fetching every `VEHICLE_REFRESH_INTERVAL` seconds (default: 30s) to pick up route reassignments.
3. **On cache miss:** If a position arrives for a `vehicle_id` not in the mapping, the service logs and skips that position. The periodic refresh will pick up the vehicle on its next cycle.

### When does it fetch route stops?

Route stops are fetched from `GET /api/v1/routes/{route_id}` using the same `RouteCache` pattern as gps_service (`route_cache/cache.py`):

- **Cache TTL:** 60 seconds (same default as gps_service).
- **On first position for a route:** Cache miss triggers HTTP fetch.
- **On expiry:** Transparent refresh on next access.

### What happens if a vehicle is on a route the service has not yet cached?

The route is fetched on demand. During the fetch, if the fetch fails (network error, 404), the event is **logged and skipped** — no crash, no retry for that specific tick. The next position event will retry the fetch.

### Per-vehicle state

```python
@dataclass
class VehicleArrivalState:
    route_id: str | None = None
    last_lat: float | None = None
    last_lng: float | None = None
    last_speed: float | None = None
    last_stop_id: str | None = None
    last_arrival_ts: float | None = None      # monotonic time of last arrival
    arrival_sequence: int = 0                  # incremented per arrival, per vehicle
    onboard: int = 0                           # current passenger count
    last_position_ts: str | None = None        # ISO timestamp from last position event
```

### Pseudocode for the detection loop

```python
async def on_position_event(msg: PositionPayload) -> None:
        vehicle_id = msg.vehicle_id
        tenant_id = msg.tenant_id

        # 1. Route lookup
        vehicle_info = vehicle_map.get(vehicle_id)
        if vehicle_info is None or vehicle_info.route_id is None:
            log.debug("Vehicle %s unknown; skipping", vehicle_id)
            return
        route_id = vehicle_info.route_id

        # 2. Route stops (cached)
        try:
            stops = await route_cache.get_route_stops(route_id, service_token)
        except Exception:
            log.exception("Route fetch failed for %s", route_id)
            return
        if len(stops) < 2:
            return

        # 3. Per-vehicle state, resetting on route change
        state = vehicle_states.get(vehicle_id)
        if state is None or state.route_id != route_id:
            state = VehicleArrivalState(route_id=route_id)
            vehicle_states[vehicle_id] = state

        # 4. Find the nearest stop within radius, at low speed
        now_mono = time.monotonic()
        for stop in stops:
            dist = haversine_distance(msg.lat, msg.lng, stop.latitude, stop.longitude)
            if dist > STOP_ARRIVAL_RADIUS_M:
                continue
            if msg.speed > STOP_SPEED_THRESHOLD_KMH:
                continue

            # Debounce
            if (
                state.last_stop_id == stop.stop_id
                and state.last_arrival_ts is not None
                and (now_mono - state.last_arrival_ts) < STOP_COOLDOWN_SECONDS
            ):
                continue

            # --- ARRIVAL DETECTED ---
            state.arrival_sequence += 1
            state.last_stop_id = stop.stop_id
            state.last_arrival_ts = now_mono

            boardings, alightings = simulate_passengers(
                state=state, stop=stop, stops=stops,
                vehicle_id=vehicle_id,
                seating_capacity=vehicle_info.seating_capacity,
            )
            state.onboard = state.onboard + boardings - alightings

            event = build_occupancy_event(
                vehicle_id=vehicle_id, tenant_id=tenant_id,
                stop_id=stop.stop_id, route_id=route_id,
                onboard=state.onboard, boardings=boardings,
                alightings=alightings,
                arrival_sequence=state.arrival_sequence,
                position_timestamp=msg.timestamp,
            )
            publisher.publish(
                topic=f"gps/{tenant_id}/{vehicle_id}/occupancy",
                payload=event,
                qos=1,
            )
            break  # at most one arrival per position event

        # 5. Update state
        state.last_lat = msg.lat
        state.last_lng = msg.lng
        state.last_speed = msg.speed
        state.last_position_ts = msg.timestamp
```
## 4. Idempotency Key

### Decision: `(vehicle_id, stop_id, arrival_sequence)`

Every occupancy event includes an `idempotency_key` field with value `"{vehicle_id}:{stop_id}:{arrival_sequence}"`.

`arrival_sequence` is a monotonically increasing integer per vehicle, incremented on each detected stop arrival. It is seeded from the backend at startup (see "Restart handling" below) and never resets during normal operation.

### Why this design

| Candidate | Pros | Cons |
|-----------|------|------|
| `(vehicle_id, stop_id, arrival_sequence)` | Deterministic, no clock dependency, naturally ordered, simple | Resets on restart; a vehicle revisiting the same stop gets a new sequence, not a collision |
| `(vehicle_id, stop_id, timestamp_bucket)` | Survives restart | Bucket sizing is fragile — too large and real events collide, too small and duplicates leak through; requires clock sync |
| UUID per event | Globally unique | Provides no dedup — every retry is a new key |

### Failure modes covered

- **MQTT QoS 1 re-delivery:** Same message delivered twice → backend sees
  the same key twice → idempotent insert (`INSERT ... ON CONFLICT
  (idempotency_key) DO NOTHING`).
- **Slow subscriber:** The key is in the payload — no timing dependency.

### Failure modes NOT covered

- **Two instances of passenger_service running** would produce conflicting
  sequences. This design assumes a single instance per tenant (same as
  gps_service). See "Known limitations" in §12.

### Restart handling

`arrival_sequence` is **seeded from the backend on startup** to prevent
post-restart key collisions. Without seeding, a restart mid-day would
reset the counter to 0, and the first few arrivals would produce keys that
collide with pre-restart events for the same `(vehicle_id, stop_id)` —
silently dropping real events via `ON CONFLICT DO NOTHING`.

**Implementation:** the backend exposes a new endpoint:

    GET /api/v1/vehicles/{vehicle_id}/latest-arrival-sequence
    → {"data": {"arrival_sequence": 47}}

The service calls this once per known vehicle at startup (after the
initial vehicle-map fetch) and initialises each `VehicleArrivalState`
with the returned sequence. If the endpoint returns 404 for a vehicle
(no events yet), the sequence starts at 0.

**Backend requirement:** the `boarding_records` table must retain at
least the latest sequence per vehicle. This is satisfied naturally by the
append-only log — a small query finds the max sequence per vehicle.

---

## 5. Occupancy Event Schema

```python
class OccupancyEvent(BaseModel):
    """Wire format for occupancy events published to MQTT."""

    vehicle_id: str                          # Backend vehicle ID
    tenant_id: str                          # Tenant for multi-tenant isolation
    stop_id: str                            # Stop where the arrival was detected
    route_id: str                           # Route the vehicle is currently on
    onboard: int = Field(ge=0)              # Total passengers after this stop
    boardings: int = Field(ge=0)            # Passengers who boarded at this stop
    alightings: int = Field(ge=0)           # Passengers who alighted at this stop
    arrival_sequence: int = Field(ge=0)     # Monotonic per-vehicle arrival counter
    position_timestamp: str                 # ISO 8601 — from the triggering position event
    service_timestamp: str                  # ISO 8601 — when passenger_service emitted this
    source: str = "passenger_service"       # Fixed string for provenance
    idempotency_key: str                    # "{vehicle_id}:{stop_id}:{arrival_sequence}"
```

### Timestamp design

The event carries **both** timestamps:

- **`position_timestamp`**: The timestamp from the GPS position event that triggered this arrival detection. This is the "ground truth" time — when the vehicle was at that location. Useful for audit and for aligning position and occupancy events chronologically.

- **`service_timestamp`**: When passenger_service processed the event and emitted the occupancy update. This is the "processing truth" time. Useful for latency monitoring (`service_timestamp − position_timestamp` = processing lag).

The backend should use `position_timestamp` for `recorded_at` in `boarding_records` to maintain chronological consistency with telemetry data.

### Where does `onboard` come from on the first event for a vehicle?

`onboard` is **seeded from the backend at startup**, alongside
`arrival_sequence`.

**Implementation:** extend the startup fetch to include the current
occupancy for each vehicle. The existing `GET /api/v1/vehicles?status=active`
response already carries `currentOccupancy` (see the backend's vehicle
schema); the service reads it during the initial vehicle-map build and
initialises `VehicleArrivalState.onboard` from that value.

For vehicles where `currentOccupancy` is 0 or absent (new vehicle, or
first run), `onboard` starts at 0 — consistent with a vehicle departing
the terminus empty.

### Why this matters

Without seeding, a restart mid-route causes the next occupancy event to
report a suddenly-dropped `onboard` value (e.g. 30 → 5), which:

- Updates `vehicles.current_occupancy` to an incorrect value in the DB.
- Renders visibly wrong on the frontend (bus appears to empty out).
- Can suppress a legitimate capacity alert that would have fired with the
  correct value.

Seeding adds one HTTP round-trip per vehicle at startup. Given the demo
fleet is O(10) vehicles and the endpoint is the same one already being
called, the cost is negligible.

------
## 6. State and Restart Model

### Decision: In-memory only, seeded from the backend on startup

Per-vehicle state (`VehicleArrivalState`) is held in a Python dictionary,
keyed by `vehicle_id`. No persistence to disk or Redis.

On startup, state is **seeded from the backend**:
- `arrival_sequence` — from `GET /api/v1/vehicles/{id}/latest-arrival-sequence`
- `onboard` — from `currentOccupancy` in the existing vehicle-list fetch

See §4 ("Restart handling") and §5 ("Where does `onboard` come from") for
the seeding mechanics. This section covers the storage decision.

### Justification

1. **Simplicity.** `gps_service` uses file persistence (`state_manager.py`)
   because it tracks complex simulation state (`next_stop_index`, dwell ticks,
   fuel) that took many ticks to build up and cannot be reconstructed from a
   single API call. `passenger_service`'s state is lightweight — two integers
   and a stop id — and is fully recoverable from the backend.

2. **The backend is the source of truth.** `arrival_sequence` is derived from
   what the backend has already recorded in `boarding_records`. `onboard` is
   derived from what the backend has already recorded in
   `vehicles.current_occupancy`. Persisting a second copy in `passenger_service`
   would create a second source of truth — the exact problem the seeding
   approach avoids.

3. **No infrastructure dependency.** No Redis to provision, no state file to
   manage, no disk I/O in the hot path.

4. **Recovery is bounded.** Startup cost is one HTTP round-trip per known
   vehicle for `arrival_sequence`, folded into the vehicle-map fetch for
   `onboard`. With a demo-scale fleet of O(10) vehicles this adds well under
   a second to startup.

### What is lost on ungraceful restart

**During the outage** (from crash to restart): all position events in that
window are missed. Any stop arrivals that occurred are lost — not
deferred. This is inherent to a live-subscription model with no persistent
message queue; recovery requires backfilling from a source that recorded
the positions (e.g. the backend's own position updates), which is out of
scope for v1.

**On restart**: nothing that was recorded in the backend is lost.

| State field | Recovered on restart? | From | Notes |
|---|---|---|---|
| `arrival_sequence` | Yes | `GET /api/v1/vehicles/{id}/latest-arrival-sequence` | Max sequence recorded for that vehicle. |
| `onboard` | Yes | `currentOccupancy` in `GET /api/v1/vehicles?status=active` | Matches the last committed value. |
| `last_stop_id` / `last_arrival_ts` | No | — | Debounce resets. One extra arrival event at most after restart, absorbed by the idempotency key (unless the sequence has also advanced — see below). |
| `last_lat` / `last_lng` / `last_speed` | No | — | Re-derived from the next position event. |
| `route_id` | Yes | Vehicle-map fetch | Same source as `onboard`. |

**Residual risk on restart:** if a vehicle was *at* a stop when the service
crashed, and it is *still* at the same stop when the service restarts, the
arrival could fire twice — once with sequence N (pre-restart), once with
sequence N+1 (post-restart), producing two records in `boarding_records`
for the same physical stop event. The idempotency key differs because the
sequence advanced, so `ON CONFLICT DO NOTHING` does not catch it. At demo
scale this is cosmetic; noting it as a known limitation (§12).

### Why not seed `last_stop_id` / `last_arrival_ts`?

Could do — `boarding_records` already records the last `stop_id` and its
`position_ts` per vehicle. If the restart is quick enough that the vehicle
hasn't moved, seeding these fields would suppress the spurious double-fire.
But the complexity (a second seeding endpoint, handling the "vehicle has
moved on" case) isn't worth it for v1. The residual-risk note above
documents the tradeoff.

---

## 7. Simulation Rules

### Core principles

1. **Deterministic given a seed.** All randomness uses Python's `random.Random` instance seeded per-vehicle. The seed is derived from `hash(vehicle_id + str(arrival_sequence))` so results are reproducible in tests.

2. **Constrained by reality.**
   - `alightings <= onboard` (cannot alight more passengers than are aboard).
   - `onboard + boardings - alightings >= 0` (occupancy never negative).
   - `onboard + boardings <= seating_capacity * CRUSH_CAPACITY_FACTOR` (mirrors the existing `CRUSH_CAPACITY_FACTOR = 1.15` in `passenger_simulation.py`).

3. **Stop-type weighted.**
   - **Terminus (first stop, index 0):** Heavy boarding (5–15 passengers), minimal alighting (0–2).
   - **Last stop:** Heavy alighting (60–90% of onboard), minimal boarding (0–3).
   - **Mid-route:** Moderate both. Boardings: 1–8, Alightings: 1–min(6, onboard).

4. **Not time-of-day weighted** in the initial implementation. This is a simulation concern, not a correctness concern. Time-of-day weighting can be added as an enhancement without changing the event schema or detection logic.

### Pseudocode

```python
def simulate_passengers(
    state: VehicleArrivalState,
    stop: RouteStop,
    stops: list[RouteStop],
    vehicle_id: str,
    seating_capacity: int = 45,
) -> tuple[int, int]:
    """Return (boardings, alightings) for a stop arrival."""
    rng = Random(f"{vehicle_id}:{state.arrival_sequence}")
    crush_cap = int(seating_capacity * CRUSH_CAPACITY_FACTOR)
    onboard = state.onboard

    stop_index = next(
        (i for i, s in enumerate(stops) if s.stop_id == stop.stop_id), -1
    )
    is_terminus = stop_index == 0
    is_last = stop_index == len(stops) - 1

    # Alightings
    if is_terminus:
        alightings = rng.randint(0, min(2, onboard))
    elif is_last:
        # Most passengers get off at the last stop
        alightings = rng.randint(
            int(onboard * 0.6), max(int(onboard * 0.6), min(onboard, int(onboard * 0.9)))
        )
    else:
        alightings = rng.randint(0, min(6, onboard))

    after_alight = onboard - alightings

    # Boardings
    remaining_capacity = max(0, crush_cap - after_alight)
    if is_terminus:
        boardings = rng.randint(5, min(15, remaining_capacity))
    elif is_last:
        boardings = rng.randint(0, min(3, remaining_capacity))
    else:
        boardings = rng.randint(1, min(8, max(1, remaining_capacity)))

    return boardings, alightings
```

### Testability

- Seeded RNG means each `(vehicle_id, arrival_sequence)` pair produces a fixed result.
- Unit tests can assert expected boardings/alightings for known seeds.
- No external I/O in the simulation function — pure calculation.

---
## 8. Backend Consumption Design

### Subscription

The backend adds a second MQTT subscription: `gps/+/+/occupancy`, handled by
a new subscriber parallel to the existing `gps/+/+/position` subscriber. Each
subscriber validates against its own Pydantic schema and hands off to its own
async DB writer via `asyncio.run_coroutine_threadsafe`, matching the existing
`GPSMQTTSubscriber` pattern.

### Data model changes

Two writes per occupancy event:

1. **Append-only audit log** — new table `boarding_records`:

       id                UUID PK
       tenant_id         VARCHAR FK -> tenants.id
       vehicle_id        VARCHAR FK -> vehicles.id
       stop_id           VARCHAR
       route_id          VARCHAR
       boardings         INTEGER
       alightings        INTEGER
       onboard_after     INTEGER
       idempotency_key   VARCHAR UNIQUE
       position_ts       TIMESTAMPTZ
       service_ts        TIMESTAMPTZ
       created_at        TIMESTAMPTZ DEFAULT now()

   The `idempotency_key` UNIQUE constraint is what makes ingestion idempotent.
   Insert uses `INSERT ... ON CONFLICT (idempotency_key) DO NOTHING`.

2. **Materialized current occupancy** — update `vehicles.current_occupancy`
   to the event's `onboard` value, and `vehicles.updated_at = now()`.

### Transaction boundary

Both writes happen in a single transaction. If the audit insert conflicts
(duplicate delivery), the `vehicles` update is skipped too — the assumption
is that the first delivery already updated `vehicles`. This avoids the
pathological case where a duplicate arrives after newer events and clobbers
`current_occupancy` with a stale value.

### Failure handling

- **Validation error** (Pydantic): log at ERROR, drop. Do not retry — the
  message is malformed, retrying won't help.
- **DB error** (transient): log at ERROR, drop. MQTT QoS 1 will not
  redeliver to a subscriber that already ACKed. If retry is needed later,
  add a dead-letter queue; out of scope for v1.
- **Unknown vehicle/tenant**: log at WARNING, drop. Do not auto-create;
  the simulator and the backend must agree on the fleet.

### WebSocket broadcast

After a successful commit, broadcast an `occupancy_update` message on the
existing WebSocket channel so the frontend can update occupancy indicators
live. Schema:

    {"type": "occupancy_update", "vehicle_id": ..., "onboard": ..., "stop_id": ...}

Exact WebSocket envelope shape should mirror the existing position broadcast.

## 9. Alert Behavior — Deferred

The backend currently runs `SELECT ... FROM alerts WHERE type = 'delay' ...`
per vehicle. Reading the code shows this is triggered from
`backend/app/services/route_tracking_service.py` when position updates are
processed — it is a *consumer* of position events, not a simulator.

**Decision: alerts stay in the backend. Not in scope for passenger_service.**

Rationale:

1. **Alerts are business rules, not simulation.** The simulator's job is to
   invent plausible data; deciding whether a vehicle is delayed requires
   comparing against the schedule, which is a domain concern the backend
   already owns.
2. **Alerts are not tied to passenger data.** The delay detection uses only
   position and route information. Splitting it into a service would create
   a service that duplicates gps_service's inputs and adds no isolation value.
3. **Backend already has the alert infrastructure.** Alerts table, dedup
   logic, acknowledge endpoint, WebSocket notification. Moving this out
   would be a rewrite with no functional benefit.

If a future requirement is "alerts must be independently deployable/scalable,"
that's the trigger to extract them into an `alert_service`. Not now.

### Capacity alerts — new, driven by occupancy

The existing alert system has a `capacity` type (or can be extended to have
one). When the backend processes an occupancy event with
`onboard >= seating_capacity * CAPACITY_ALERT_THRESHOLD` (suggest 0.9), it
emits a capacity alert, deduplicated per `(vehicle_id, type='capacity')` for
a window of e.g. 5 minutes. This is a small addition to the existing alert
service, not a new subsystem.

The threshold constant should live next to the existing alert thresholds;
`CRUSH_CAPACITY_FACTOR` (currently 1.15) is the hard ceiling; the alert
threshold (0.9) is softer and earlier.

## 10. Backend Deletion Plan

**Before deleting anything, the following must be verified by reading the
actual code and listing each function/class/module with file path. The list
below is derived from the design phase's read of the repo; confirm before
removing.**

### To delete (simulation code made redundant by passenger_service)

| Path | What it does | Delete after |
|---|---|---|
| `backend/app/services/passenger_simulation.py` | The whole module: generated boardings/alightings per stop | Occupancy subscriber is live and producing records |
| Any scheduled task / background loop that calls into `passenger_simulation` | Whatever drove the simulation tick | Same |
| `backend/tests/test_passenger_simulation.py` (or equivalent) | Tests for the above | Same as above |

### To keep (not simulation)

| Path | Why it stays |
|---|---|
| `backend/app/services/route_tracking_service.py` | Delay detection — business rule, consumes position events, not a simulator |
| `backend/app/services/alert_service.py` (or equivalent) | Alert generation, dedup, acknowledge — business logic |
| `backend/app/services/gps_mqtt_subscriber.py` | Existing position consumer — extended, not replaced |
| All vehicle/route/stop CRUD | Data ownership, not simulation |
| Loop counting logic (`planned_loops`, `completed_loops`) | Needs review: is this simulation or derived from position events? If simulation, it moves to gps_service (which already tracks position); if derived, it stays. **Open question §11.** |

### The new code to add (not a deletion, but part of the same change)

- `backend/app/services/occupancy_mqtt_subscriber.py` — new subscriber
- `backend/app/services/occupancy_service.py` — writes to `boarding_records`,
  updates `vehicles.current_occupancy`, triggers capacity alerts
- `backend/app/schemas/occupancy.py` — `OccupancyEvent` Pydantic model
- `backend/app/models/boarding_record.py` — SQLAlchemy model
- Alembic migration for `boarding_records`

### Verification that nothing broke

After deletion:

1. Run `docker compose up --build`.
2. Wait for one full route loop (a few minutes with the demo's tick interval).
3. Query: `SELECT COUNT(*) FROM boarding_records;` — should be growing.
4. Query: `SELECT vehicle_id, current_occupancy FROM vehicles;` — should
   show plausible non-zero values for active vehicles.
5. Frontend: occupancy indicator on the map should update live.
6. Confirm no `passenger_simulation` references remain:
   `rg "passenger_simulation" backend/`.

## 11. Open Questions

| # | Question | Recommended default | Impact if wrong |
|---|---|---|---|
| 1 | Should `arrival_sequence` be seeded from the backend on startup? | **Resolved: yes.** Backend exposes `GET /api/v1/vehicles/{id}/latest-arrival-sequence`; service seeds at startup. | — |
| 2 | Should `onboard` be seeded from `vehicles.current_occupancy` on first event? | **Resolved: yes.** Read `currentOccupancy` from the existing vehicle-list fetch. | — |
| 3 | Is loop counting (`completed_loops`) simulation or derived? | **Defer to gps_service.** It already tracks position; loop detection is a position concern, not a passenger one. | Low — cosmetic; not demo-critical. |
| 4 | Should the audit log be partitioned or pruned (it grows forever)? | **Defer.** Demo scale doesn't need it. | Low. |
| 5 | Should `onboard` be allowed to exceed `seating_capacity`? | **Yes, up to `CRUSH_CAPACITY_FACTOR * seating_capacity`.** Mirrors existing simulator constant. | Low — cosmetic; a bus with 50/45 seated is realistic. |
| 6 | What if two position events both trigger arrivals at different stops on the same tick? | **Only fire one arrival per position event** (the `break` in the loop). | Low — the other stop will fire on the next event if the vehicle remains near it. |
| 7 | Determinism of `random.Random(seed_string)` across Python versions. | **Use a stable hash (`hashlib.sha256`) to derive the seed int.** | Medium — tests pinned to golden values would break on Python upgrade. |
| 8 | Should `passenger_service` expose a REST API beyond health/status? | **No.** Debug via `/status` only. | Low. |
| 9 | What happens if the position stream stalls (all vehicles stop moving)? | **Service idles; no events fire.** Health endpoint stays green. | Low. |
| 10 | Should the backend reject occupancy events for vehicles it doesn't know? | **Yes.** Log warning, drop. Never auto-create. | Low. |


## 12. Known Limitations

Explicit assumptions and constraints for v1. These are not bugs — they are
deliberate tradeoffs accepted to keep the demo scope bounded. Any of them
can become a follow-up task if requirements change.

### Architecture

- **Single instance per tenant.** The `arrival_sequence` counter and
  in-memory state assume exactly one `passenger_service` process per
  tenant. Running two instances would produce conflicting sequences and
  interleaved occupancy events. Scaling to multiple instances requires
  moving `arrival_sequence` to a shared store (Redis counter or DB
  sequence) or sharding by vehicle ID.

- **No failover.** If `passenger_service` crashes, no occupancy events
  are produced until it restarts. On restart, seeding recovers
  `arrival_sequence` and `onboard`, but stop arrivals that occurred during
  the outage are lost. This is acceptable for a simulator.

### Data consistency

- **Occupancy and vehicle state can drift on partial failure.** The
  backend writes to `boarding_records` and updates
  `vehicles.current_occupancy` in one transaction, so within a single
  event they stay consistent. But if a downstream consumer (e.g. the
  frontend) reads them at different moments, it may observe a mismatch
  for up to one event's processing time.

- **Restart visibility.** Even with seeding, a restart is visible: the
  first post-restart occupancy event's `service_timestamp` lags the
  triggering `position_timestamp` by the restart duration. Consumers
  correlating the two timestamps should tolerate gaps.

- **Clock skew.** Timestamps are UTC and assume NTP-synced hosts. A
  significant skew between `gps_service` and `passenger_service` will
  make `service_timestamp − position_timestamp` unreliable, though
  ordering within a service is preserved.
- **Restart may double-fire a stop arrival.** If a vehicle is at a stop
  when `passenger_service` crashes and is still there at restart, the
  arrival fires once more after seeding (with `arrival_sequence + 1`).
  The idempotency key differs, so both records persist. Cosmetic at demo
  scale. To fix: seed `last_stop_id` and `last_arrival_ts` alongside
  `arrival_sequence` (deferred — see §6).

### Scale

- **No backpressure.** At demo scale (a few vehicles, 5s tick) this is
  irrelevant. At 1,000+ vehicles or 1s ticks, the broker would buffer
  and eventually drop for a slow subscriber. Handling requires a
  dead-letter queue and a consumer-lag monitor.

- **No persistence of the audit log beyond the backend DB.** The service
  itself stores nothing on disk. A broker restart during a service outage
  loses in-flight events.

### Detection

- **Stop radius is a fixed 30m.** Urban canyons, GPS noise, and multi-lane
  roads with parallel stops may cause missed or misattributed arrivals.
  A production system would use map-matching or per-stop geofences.

- **No handling for two stops within detection radius.** The loop
  `break`s after the first match; if two stops are within 30m, the one
  appearing first in the route's stop list wins. Verify seed data does
  not place stops this close.

- **Arrival detection depends on speed.** Vehicles that report `speed = 0`
  while moving (bad GPS data) will spuriously trigger. Not a concern for
  the simulator, since it controls speed.

### Simulation

- **RNG is deterministic per `(vehicle_id, arrival_sequence)`.** This is
  good for testing but means two runs with the same inputs produce
  identical passenger counts. Fine for demos; a "randomised demo" mode
  would need a different seed source.

- **No time-of-day modelling.** Rush hour and off-peak produce the same
  boarding distributions. Acceptable for v1; noted in §7 as an
  enhancement.
