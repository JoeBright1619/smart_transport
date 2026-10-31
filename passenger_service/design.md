# Passenger Service — Design Document

## 1. Architecture Diagram

```text
 gps_service ───────────────┐
   (simulated positions)    │ publish gps/{t}/{v}/position
                            ▼
                    ┌───────────────┐   subscribe …/position    ┌────────────────────┐
                    │  MQTT broker  │──────────────────────────►│ passenger_service  │
                    │               │◄──────────────────────────│                    │
                    └───────┬───────┘   publish …/occupancy     └─────────┬──────────┘
                            │ subscribe …/position, …/occupancy           │ HTTP (see flow table)
                            ▼                                             ▼
                    ┌─────────────────────────────────────────────────────────┐
                    │ backend  (FastAPI + PostgreSQL + WebSocket)             │
                    │   occupancy_events · boarding_passenger_events          │
                    │   vehicles.current_occupancy · capacity alerts · WS     │
                    └─────────────────────────────────────────────────────────┘
```

Inside `passenger_service`:

```text
 MQTT subscriber (position events)
        │  run_coroutine_threadsafe
        ▼
 ArrivalOrchestrator ──► stop-arrival detector (pure)
        │            ──► passenger simulation engine (pure)
        │            ──► occupancy event builder
        │            ──► MQTT publisher (occupancy events)
        │
        ├── route_cache (HTTP, TTL 60s)
        ├── vehicle map (HTTP, refreshed every VEHICLE_REFRESH_INTERVAL)
        ├── passenger pool (HTTP, tenant-wide, refreshed every VEHICLE_REFRESH_INTERVAL)
        ├── arrival-sequence client (HTTP, once per vehicle on first sight)
        └── FastAPI (/health, /status only)
```

### Message flows

| #   | From              | To                | Transport                                                      | Payload                                                                          |
| --- | ----------------- | ----------------- | -------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| 1   | backend           | gps_service       | HTTP (`/api/v1/vehicles`, `/api/v1/service/whoami`)            | Vehicle list, tenant identity                                                    |
| 2   | backend           | gps_service       | HTTP (`/api/v1/routes/{id}`)                                   | Route stops                                                                      |
| 3   | gps_service       | MQTT broker       | MQTT publish `gps/{tenant}/{vehicle}/position`                 | `GPSPositionUpdate` payload                                                      |
| 4   | MQTT broker       | backend           | MQTT subscribe `gps/+/+/position`                              | same                                                                             |
| 5   | MQTT broker       | passenger_service | MQTT subscribe `gps/+/+/position`                              | same                                                                             |
| 6   | backend           | passenger_service | HTTP (`/api/v1/routes/{id}`)                                   | Route stops                                                                      |
| 7   | backend           | passenger_service | HTTP (`/api/v1/service/vehicles?status=active`)                | Vehicle list incl. `route_id`, `tenantId`, `seatingCapacity`, `currentOccupancy` |
| 8   | backend           | passenger_service | HTTP (`/api/v1/passengers`)                                    | Passenger ID pool (**universal**, not tenant-scoped — see §7)                    |
| 9   | backend           | passenger_service | HTTP (`/api/v1/service/vehicles/{id}/latest-arrival-sequence`) | Max `arrival_sequence` per vehicle                                               |
| 10  | passenger_service | MQTT broker       | MQTT publish `gps/{tenant}/{vehicle}/occupancy`                | `OccupancyEvent` payload                                                         |
| 11  | MQTT broker       | backend           | MQTT subscribe `gps/+/+/occupancy`                             | same                                                                             |

Row 8 fetches the **universal** passenger pool. Passengers in this system
are not tenant-bound: a real user can board vehicles of any tenant.
`passenger_service` therefore fetches the pool once, process-wide, and
never passes a `tenant_id` to the pool endpoint. Tenant scoping applies
to _vehicles_, not to _passengers_. See §7 ("Universal passengers").

### Latency and consistency

**Expected end-to-end lag for occupancy events:** ~5–15 seconds from the
physical event (bus at stop) to the backend DB commit. Composition:

| Stage                                    | Typical                            | Notes                                                                                            |
| ---------------------------------------- | ---------------------------------- | ------------------------------------------------------------------------------------------------ |
| gps_service tick interval                | up to `POLL_INTERVAL` (default 5s) | The simulator publishes once per tick; a bus arriving just after a tick waits one full interval. |
| MQTT publish → passenger_service receive | <100ms                             | Same broker, QoS 1.                                                                              |
| Detection + simulation                   | <50ms                              | Pure calculation, plus one cached route lookup.                                                  |
| MQTT publish → backend receive           | <100ms                             | Same broker, QoS 1.                                                                              |
| Validation + DB transaction              | <50ms                              | Three writes, single transaction (see §8).                                                       |

POLL_INTERVAL is a gps_service setting, not a passenger_service
one; it is listed here only because it dominates the end-to-end latency
budget.

**Guarantees:**

- **At-least-once delivery on the MQTT hops** (QoS 1 on both). Duplicates are
  possible; the idempotency key makes ingestion idempotent.
- **Consumer-side processing is at-most-once on DB failure in v1.** The backend
  drops an event after a transient DB error (see §8 "Failure handling"), so the
  pipeline as a whole is _not_ end-to-end at-least-once until a dead-letter
  queue or retry is added.
- **Per-vehicle ordering** is preserved. MQTT QoS 1 does not guarantee global
  ordering across topics, but events for a given vehicle arrive on the same
  topic and are processed in the order published.
- **No cross-vehicle ordering guarantee.** Events from different vehicles may
  be interleaved arbitrarily.

**Best-effort, not guaranteed:**

- **Correlation between position and occupancy timestamps.** The occupancy
  event carries the triggering position's timestamp, so the two streams can
  be joined chronologically — but the _arrival_ of the two events at the
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

### Debouncing: cooldown and re-arm

Two mechanisms prevent re-firing for the same stop:

- **Cooldown.** Per-vehicle state tracks `last_stop_id` and `last_arrival_ts`.
  A new arrival at the same `stop_id` is suppressed if fewer than
  `STOP_COOLDOWN_SECONDS = 60` seconds have elapsed since the previous arrival
  at that stop. This absorbs GPS jitter at the edge of the radius.
- **Re-arm.** After an arrival fires, `state.armed` is set to `False`. It is set
  back to `True` only when a position is observed more than
  `STOP_ARRIVAL_RADIUS_M` from the last-arrived stop. A same-stop arrival is
  suppressed while `armed` is `False`, regardless of the cooldown. This handles
  a bus that dwells at a stop for longer than the cooldown (without it, a dwell
  of more than 60s would fire a second arrival for the same visit).
- Arrivals at _different_ stops are never suppressed — a bus moving rapidly
  between closely-spaced stops correctly fires two events.

Cooldown and re-arm are independent guards — either one suppresses.
A bus that leaves the radius (re-arming) and returns within
STOP_COOLDOWN_SECONDS is still suppressed by the cooldown; this is
intentional (GPS jitter can bounce across the radius boundary). Do not
AND them (require both to allow).

### How does the service know which route a vehicle is on?

Each incoming position message carries `vehicle_id` and `tenant_id`. The service maintains a **vehicle-to-route mapping** that it populates by:

1. **On startup:** Fetching active vehicles from `GET /api/v1/service/vehicles?status=active` — the tenant-agnostic fleet endpoint added in backend Task 3.0. Auth: universal service token with `vehicles:read_universal` scope (the `/api/v1/vehicles` endpoint is tenant-anchored and rejects universal tokens). Each vehicle record includes `route_id`, `tenantId`, `seatingCapacity` and `currentOccupancy`.
2. **Periodically:** Re-fetching every `VEHICLE_REFRESH_INTERVAL` seconds (default: 30s) to pick up route reassignments and new vehicles. Vehicles that disappear from the map have their state dropped and their real passenger IDs released (see §7).
3. **On cache miss:** If a position arrives for a `vehicle_id` not in the mapping, the service logs and skips that position. The periodic refresh will pick up the vehicle on its next cycle.

### When does it fetch route stops?

Route stops are fetched from `GET /api/v1/routes/{route_id}` using the same `RouteCache` pattern as gps_service (`route_cache/cache.py`):

- **Cache TTL:** 60 seconds (same default as gps_service).
- **On first position for a route:** Cache miss triggers HTTP fetch.
- **On expiry:** Transparent refresh on next access.

### What happens if a vehicle is on a route the service has not yet cached?

The route is fetched on demand. During the fetch, if the fetch fails (network error, 404), the event is **logged and skipped** — no crash, no retry for that specific tick. The next position event will retry the fetch.

### Inputs

`PositionEvent` (passenger_service/models/position.py) is the parsed inbound MQTT position message published by gps_service. It is a Pydantic v2 BaseModel with exactly six fields, all named in snake_case to match both the design and the wire: `vehicle_id, tenant_id, lat, lng, speed, timestamp`. The wire contract is owned by `gps_service/mqtt/payload.py` (to_backend_payload), which mirrors the backend's GPSPositionUpdate schema; its field names are snake_case and require no aliases. lat and lng are constrained to [-90, 90] and [-180, 180]; speed is constrained to >= 0; timestamp is an ISO 8601 datetime. The wire carries additional fields (device_id, heading, fuel, engine_status, source) that PositionEvent intentionally does not model; they are ignored on parse (extra="ignore"). The two services mirror each other's conventions but do not share code — position.py imports nothing from gps_service.
Its fields are:
stop_id: str
latitude: float # -90..90
longitude: float # -180..180
sequence: int # >= 0; route-defined order

There is **no `stop_index` field**. The design's earlier use of `stop_index` was a spec bug; every reference to it has been replaced by `sequence`. The simulation compares `dest_sequence == current_sequence`, not array indices. This makes the logic robust to gapped route data (e.g. sequence values `[0, 1, 3]` after a stop deletion).

**Sortedness requirement.** `stops` is passed to `detect_arrival` and `simulate_passengers` **sorted by `sequence`**. The route cache guarantees this by sorting after fetch (see the route-cache note in §3 "When does it fetch route stops?"); the detector and simulation may _assume_ it. Because of this guarantee, `sequence` and array position coincide for contiguous route data — but the code must use `sequence`, not the array index, so that a backend sending gaps does not silently corrupt destinations.

### Return value of `detect_arrival`

`detect_arrival(...)` returns a `RouteStop | None` — the arriving stop, or `None`. There is no index in the return value; callers use `stop.sequence` when they need the ordinal position and `stop.stop_id` when they need the join key. The simulation compares `sequence` values, not array positions.

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
    armed: bool = True                         # False after an arrival until the bus leaves the radius
    arrival_sequence: int = 0                  # incremented per arrival, per vehicle; never reset
    onboard: int = 0                           # current passenger count (== len(passengers) once synthesised)
    needs_synthesis: bool = False              # True when onboard > 0 but passengers is empty (seeded/route change)
    last_position_ts: datetime | None = None   # datetime from last position event (PositionEvent.timestamp)
    passengers: list[dict] = field(default_factory=list)
        # Each entry: {"origin_sequence": int, "dest_sequence": int,
        #              "distance_km": float, "passenger_id": str | None}
        # See §7 "Per-passenger record"; fields are RouteStop.sequence
        # values, not array indices.
    current_trip_id: str | None = None         # threaded through in v1, always None (see §12)
```

`last_stop_id` is a `RouteStop.stop_id` string, not an index or a
sequence. It is the join key against `occupancy_events.stop_id` and is
what the debounce logic compares. The cooldown and re-arm logic never
needs the sequence — only the ID and the coordinates.

There is **no per-vehicle passenger pool and no per-tenant pool**. The pool
is **universal** (process-wide), cached by a single fetcher, and handed to
the simulation engine as an argument (§7). Passengers are not tenant-bound:
the same real passenger ID can be assigned to a vehicle of any tenant. The
global "one bus at a time" invariant (§7 rule 4) is therefore also global,
not per-tenant — which it already was in the design, but the old wording
("tenant-wide") obscured.

`VehicleSeed(arrival_sequence: int = 0, onboard: int = 0)` carries the values
fetched from the backend for a vehicle's first appearance.

`VehicleStateStore` holds `dict[str, VehicleArrivalState]`:

- `has(vehicle_id) -> bool`
- `get_or_create(vehicle_id, route_id, seed: VehicleSeed | None = None) -> StateLookup`
  where `StateLookup = (state, released_ids)`.
  - **New vehicle:** builds fresh state from `seed` (`arrival_sequence`,
    `onboard`); sets `needs_synthesis = onboard > 0`.
  - **Route change:** keeps `arrival_sequence` and `onboard`; clears
    `passengers`, `last_stop_id`, `last_arrival_ts`, `last_*` observations and
    re-arms; sets `needs_synthesis = onboard > 0`; returns the real passenger
    IDs that were on the old list as `released_ids` so the caller can free them.
  - **Same route:** returns the existing state with `released_ids = []`.
- `remove(vehicle_id) -> list[str]` — drops the state and returns its real IDs.

`arrival_sequence` is never reset by a route change. Resetting it would
reintroduce the key collisions that seeding exists to prevent (§4).

### Pseudocode for the orchestrator

The orchestrator is the only component that mutates state and the global
passenger set. `detect_arrival` and `simulate_passengers` are pure.

```python
class ArrivalOrchestrator:
    def __init__(self, *, state_store, route_cache, vehicle_map, sequence_client,
                 pool_fetcher, publisher, settings, service_token):
        ...
        self._globally_on_board: set[str] = set()   # real passenger IDs currently on any bus

    async def handle_position(self, position: PositionEvent) -> None:
        # 1. Route lookup
        info = self._vehicle_map.get(position.vehicle_id)
        if info is None or info.route_id is None:
            log.debug("Vehicle %s unknown; skipping", position.vehicle_id)
            return

        # 2. Route stops (cached)
        try:
            stops = await self._route_cache.get_route_stops(info.route_id, self._token)
        except Exception:
            log.exception("Route fetch failed for %s", info.route_id)
            return
        if len(stops) < 2:
            return

        # 3. Per-vehicle state: lazy seeding on first sight, preserve sequence on route change
        seed = None
        if not self._state_store.has(position.vehicle_id):
            try:
                seq = await self._sequence_client.fetch_latest_sequence(position.vehicle_id)  # 404 -> 0
            except Exception:
                log.exception("Sequence seed failed for %s", position.vehicle_id)
                return          # never guess 0 on a transient failure: could collide with stored keys
            seed = VehicleSeed(arrival_sequence=seq, onboard=info.current_occupancy)
        state, released = self._state_store.get_or_create(position.vehicle_id, info.route_id, seed)
        self._globally_on_board -= set(released)

        # 4. Detect (pure), then apply
        now_mono = time.monotonic()
        arrival = detect_arrival(position, stops, state, now_mono, self._settings)
        if arrival is not None:
            state.arrival_sequence += 1
            state.last_stop_id = arrival.stop_id
            state.last_arrival_ts = now_mono
            state.armed = False

            rng = make_rng(position.vehicle_id, state.arrival_sequence)
            result = simulate_passengers(
                state=state, current_sequence=arrival.sequence, stops=stops,
                seating_capacity=info.seating_capacity,
                passenger_pool=self._pool_fetcher.cached_ids(),
                excluded_ids=self._globally_on_board,
                params=self._sim_params, rng=rng,
            )
            state.passengers = result.passengers
            state.onboard = result.onboard
            state.needs_synthesis = False
            self._globally_on_board -= set(result.alighted_ids)
            self._globally_on_board |= set(result.boarded_ids)

            event = build_occupancy_event(
                vehicle_id=position.vehicle_id, tenant_id=position.tenant_id,
                stop_id=arrival.stop_id, route_id=info.route_id,
                onboard=result.onboard, boardings=result.boardings,
                alightings=result.alightings,
                arrival_sequence=state.arrival_sequence,
                position_timestamp=position.timestamp,
                boarded_passenger_ids=result.boarded_ids,
                alighted_passenger_ids=result.alighted_ids,
                revenue_delta=result.revenue_delta,
            )
            self._publisher.publish(
                topic=f"gps/{position.tenant_id}/{position.vehicle_id}/occupancy",
                payload=event, qos=1,
            )

        # 5. Update observations and re-arm
        if state.last_stop_id is not None and not state.armed:
            last_stop = next((s for s in stops if s.stop_id == state.last_stop_id), None)
            if last_stop is None or haversine_distance(
                position.lat, position.lng, last_stop.latitude, last_stop.longitude
            ) > self._settings.STOP_ARRIVAL_RADIUS_M:
                state.armed = True
        state.last_lat, state.last_lng = position.lat, position.lng
        state.last_speed = position.speed
        state.last_position_ts = position.timestamp

    def release_vehicle(self, vehicle_id: str) -> list[str]:
        """Drop per-vehicle state and release its real passenger IDs.

        Called by the periodic refresh when a vehicle leaves the map.
        Returns the released IDs (for logging/tests); they are already
        removed from self._globally_on_board.
        """
        released = self._state_store.remove(vehicle_id)
        self._globally_on_board -= set(released)
        return released
```

`detect_arrival` iterates the stops **in `sequence` order** and returns the
**first** `RouteStop` that is within radius and at low speed, is not
suppressed by cooldown/re-arm, and `None` otherwise. At most one arrival
fires per position event. "First match in route order" means first by
`sequence`, not nearest — see §12.

`detect_arrival` takes `now_mono` as a parameter and must not call
`time.monotonic()` itself — that is what keeps it pure and testable.
The orchestrator computes `now_mono` once per position event.

---

## 4. Idempotency Key

### Decision: `(vehicle_id, stop_id, arrival_sequence)`

Every occupancy event includes an `idempotency_key` field with value `"{vehicle_id}:{stop_id}:{arrival_sequence}"`.

`arrival_sequence` is a monotonically increasing integer per vehicle, incremented on each detected stop arrival. It is seeded from the backend the first time the service sees a vehicle (see "Restart handling" below) and never resets during normal operation, including across route changes.

### Why this design

| Candidate                                 | Pros                                                          | Cons                                                                                                                          |
| ----------------------------------------- | ------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `(vehicle_id, stop_id, arrival_sequence)` | Deterministic, no clock dependency, naturally ordered, simple | Requires seeding on restart (see "Restart handling"); a vehicle revisiting the same stop gets a new sequence, not a collision |
| `(vehicle_id, stop_id, timestamp_bucket)` | Survives restart without seeding                              | Bucket sizing is fragile — too large and real events collide, too small and duplicates leak through; requires clock sync      |
| UUID per event                            | Globally unique                                               | Provides no dedup — every retry is a new key                                                                                  |

### Failure modes covered

- **MQTT QoS 1 re-delivery:** Same message delivered twice → backend sees
  the same key twice → idempotent insert (`INSERT ... ON CONFLICT
(idempotency_key) DO NOTHING`).
- **Slow subscriber:** The key is in the payload — no timing dependency.
- **Restart mid-day:** seeding keeps the counter ahead of anything already stored.
- **Route reassignment mid-day:** the counter is preserved, so keys stay unique.

### Failure modes NOT covered

- **Two instances of passenger_service running** would produce conflicting
  sequences. This design assumes a single instance per tenant (same as
  gps_service). See "Known limitations" in §12.

### Restart handling

`arrival_sequence` is **seeded from the backend** to prevent
post-restart key collisions. Without seeding, a restart mid-day would
reset the counter to 0, and the first few arrivals would produce keys that
collide with pre-restart events for the same `(vehicle_id, stop_id)` —
silently dropping real events via `ON CONFLICT DO NOTHING`.

**Implementation:** the backend exposes a new endpoint:

    GET /api/v1/service/vehicles/{vehicle_id}/latest-arrival-sequence
    → 200 {"data": {"arrivalSequence": 47}}
    → 404 (error code `vehicle_not_found`)       unknown vehicle
    → 404 (error code `no_arrival_records`)      known vehicle with no occupancy events yet

The service calls this **lazily, the first time a vehicle is seen** (on its
first position event after the vehicle appears in the vehicle map), not only at
process startup. This covers vehicles that join the fleet after startup. Both
404 variants mean "start from 0". Any other failure (network error, 5xx) means
the position event is skipped and seeding is retried on the next event — the
service never falls back to 0 on a transient error, because that could collide
with stored keys.

**Backend requirement:** `occupancy_events` carries an `arrival_sequence`
column with an index on `(vehicle_id, arrival_sequence)`; the endpoint returns
`MAX(arrival_sequence)` for the vehicle, scoped to the caller's tenant.

---

## 5. Occupancy Event Schema

```python
class OccupancyEvent(BaseModel):
    """Wire format for occupancy events published to MQTT."""

    vehicle_id: str                          # Backend vehicle ID
    tenant_id: str                           # Tenant for multi-tenant isolation
    stop_id: str                             # Stop where the arrival was detected
    route_id: str                            # Route the vehicle is currently on
    onboard: int = Field(ge=0)               # Total passengers after this stop
    boardings: int = Field(ge=0)             # Passengers who boarded at this stop
    alightings: int = Field(ge=0)            # Passengers who alighted at this stop
    arrival_sequence: int = Field(ge=0)      # Monotonic per-vehicle arrival counter
    position_timestamp: str                  # ISO 8601 — from the triggering position event
    service_timestamp: str                   # ISO 8601 — when passenger_service emitted this
    source: str = "passenger_service"        # Fixed string for provenance.
                                             # Accepted by the backend schema;
                                             # not persisted in occupancy_events
                                             # (debug/audit only in v1).
    idempotency_key: str                     # "{vehicle_id}:{stop_id}:{arrival_sequence}"

    # Per-passenger attribution (§7). Optional. Empty lists mean "no real IDs
    # were assigned or released this arrival", which is indistinguishable on the
    # wire from a publisher that does not emit these fields at all. The backend
    # treats absence and empty list identically.
    boarded_passenger_ids: list[str] = Field(default_factory=list)
    alighted_passenger_ids: list[str] = Field(default_factory=list)

    # Revenue generated at this stop, in simulation units
    # (REVENUE_PER_KM * distance_km; see §7 "Revenue"). Not a real currency.
    # 0.0 when no alightings generated revenue.
    revenue_delta: float = Field(default=0.0, ge=0.0)
```

> **Delivery note.** This schema was built in two commits: the base
> fields in Task 4.4, then `boarded_passenger_ids`,
> `alighted_passenger_ids` and `revenue_delta` in Task 4.5. The
> backend schema (Task 2.1) is authored against _this_ section, not
> against whichever passenger_service commit is currently checked in.

### Timestamp design

The event carries **both** timestamps:

- **`position_timestamp`**: The timestamp from the GPS position event that triggered this arrival detection. This is the "ground truth" time — when the vehicle was at that location. Useful for audit and for aligning position and occupancy events chronologically.

- **`service_timestamp`**: When passenger_service processed the event and emitted the occupancy update. This is the "processing truth" time. Useful for latency monitoring (`service_timestamp − position_timestamp` = processing lag).

The backend stores both in `occupancy_events` and uses `position_timestamp` for
time-range queries and chronological consistency with telemetry data.

### Where does `onboard` come from on the first event for a vehicle?

`onboard` is **seeded from the backend** the first time a vehicle is seen,
alongside `arrival_sequence`.

**Implementation:** the vehicle-map fetch reads `currentOccupancy` from the
existing `GET /api/v1/service/vehicles?status=active` response (it is already part of
the backend's vehicle schema) into `VehicleInfo.current_occupancy` (default 0
when absent). On a vehicle's first appearance the orchestrator builds a
`VehicleSeed` from that value and the fetched sequence.

A seeded `onboard > 0` has no passenger records behind it, so the state is
marked `needs_synthesis`. The first arrival after seeding synthesises that many
**anonymous** passenger records (§7 "Synthesising seeded passengers") before
applying the normal alight/board rules. From then on `onboard == len(passengers)`.

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

Seeding without synthesis would be just as wrong in the other direction: the
seeded passengers would have no destinations, never alight, and `onboard` would
only grow until the crush cap.

Seeding adds one HTTP round-trip per vehicle on first sight. Given the demo
fleet is O(10) vehicles, the cost is negligible.

---

## 6. State and Restart Model

### Decision: In-memory only, seeded from the backend on first sight of each vehicle

Per-vehicle state (`VehicleArrivalState`) is held in a Python dictionary,
keyed by `vehicle_id`. No persistence to disk or Redis.

State is **seeded from the backend** when a vehicle is first seen:

- `arrival_sequence` — from `GET /api/v1/service/vehicles/{id}/latest-arrival-sequence`
- `onboard` — from `currentOccupancy` in the existing vehicle-list fetch
- `passengers` — _not_ fetched; synthesised anonymously on the first arrival (§7)

See §4 ("Restart handling") and §5 ("Where does `onboard` come from") for
the seeding mechanics. This section covers the storage decision.

### Justification

1. **Simplicity.** `gps_service` uses file persistence (`state_manager.py`)
   because it tracks complex simulation state (`next_stop_index`, dwell ticks,
   fuel) that took many ticks to build up and cannot be reconstructed from a
   single API call. `passenger_service`'s state is reconstructable from the
   backend: the two values that must be exact (`arrival_sequence`, `onboard`)
   are seeded; the passenger list is re-synthesised, and its exact contents are
   simulation detail rather than a fact the backend owns.

2. **The backend is the source of truth.** `arrival_sequence` is derived from
   what the backend has already recorded in `occupancy_events`. `onboard` is
   derived from what the backend has already recorded in
   `vehicles.current_occupancy`. Persisting a second copy in `passenger_service`
   would create a second source of truth — the exact problem the seeding
   approach avoids.

3. **No infrastructure dependency.** No Redis to provision, no state file to
   manage, no disk I/O in the hot path.

4. **Recovery is bounded.** Startup cost is one HTTP round-trip per vehicle
   for `arrival_sequence`, folded into the vehicle-map fetch for
   `onboard`. With a demo-scale fleet of O(10) vehicles this adds well under
   a second.

### What is lost on ungraceful restart

**During the outage** (from crash to restart): all position events in that
window are missed. Any stop arrivals that occurred are lost — not
deferred. This is inherent to a live-subscription model with no persistent
message queue; recovery requires backfilling from a source that recorded
the positions (e.g. the backend's own position updates), which is out of
scope for v1.

**On restart**: nothing that was recorded in the backend is lost.

| State field                                  | Recovered on restart? | From                                                               | Notes                                                                                             |
| -------------------------------------------- | --------------------- | ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------- |
| `arrival_sequence`                           | Yes                   | `GET /api/v1/service/vehicles/{id}/latest-arrival-sequence`        | Max sequence recorded for that vehicle.                                                           |
| `onboard`                                    | Yes                   | `currentOccupancy` in `GET /api/v1/service/vehicles?status=active` | Matches the last committed value.                                                                 |
| `passengers`                                 | Partially             | Synthesised                                                        | Anonymous records with random destinations; real passenger identities of those on board are lost. |
| `_globally_on_board`                         | No                    | —                                                                  | Starts empty. See §12.                                                                            |
| `last_stop_id` / `last_arrival_ts` / `armed` | No                    | —                                                                  | Debounce resets. See residual risk below.                                                         |
| `last_lat` / `last_lng` / `last_speed`       | No                    | —                                                                  | Re-derived from the next position event.                                                          |
| `route_id`                                   | Yes                   | Vehicle-map fetch                                                  | Same source as `onboard`.                                                                         |

**Residual risk on restart:** if a vehicle was _at_ a stop when the service
crashed, and it is _still_ at the same stop when the service restarts, the
arrival could fire twice — once with sequence N (pre-restart), once with
sequence N+1 (post-restart), producing two rows in `occupancy_events`
for the same physical stop event. The idempotency key differs because the
sequence advanced, so `ON CONFLICT DO NOTHING` does not catch it. At demo
scale this is cosmetic; noting it as a known limitation (§12).

### Why not seed `last_stop_id` / `last_arrival_ts`?

Could do — `occupancy_events` already records the last `stop_id` and its
`position_timestamp` per vehicle. If the restart is quick enough that the vehicle
hasn't moved, seeding these fields would suppress the spurious double-fire.
But the complexity (a second seeding endpoint, handling the "vehicle has
moved on" case) isn't worth it for v1. The residual-risk note above
documents the tradeoff.

---

## 7. Simulation Rules

The simulation mirrors the pre-existing backend simulation in `backend/app/services/passenger_simulation.py` (deleted in Phase 8), with the deliberate changes called out below. It is per-passenger, not per-count: each vehicle carries a list of passenger dicts, each with an origin stop, destination stop, route distance, and an optional real `passenger_id`.

### Universal passengers

Passengers are **not tenant-bound**. A real user may board a vehicle of
any tenant; the backend's passenger pool is universal. Consequences for
this design:

1. **The pool fetcher is tenant-agnostic.** It calls
   `GET /api/v1/passengers` (no `tenant_id`, no `role` filter) with a
   universal service token carrying `passengers:read_universal`, and
   caches one list for the whole process. There is no per-tenant pool,
   and `PassengerPoolFetcher` does not take a tenant argument. The
   pool contains all registered passengers regardless of role; role
   filtering is deliberately omitted for the demo.
2. **The exclusion set is already global, not per-tenant.** §7 rule 4
   ("Global one-bus-at-a-time") says a real passenger cannot be on two
   vehicles simultaneously — that rule was already written process-wide,
   not per-tenant, and remains correct under universal passengers. No
   code change to the exclusion logic.
3. **The vehicle map is cross-tenant; the route cache is keyed by**
   **route id (globally unique).** Vehicles belong to tenants — each row from `/api/v1/service/vehicles` carries `tenantId` — but the map itself spans all tenants because it is fetched with a universal service token (Task 3.0). Route ids are globally unique, so the route cache needs no tenant dimension. Only _passengers_ are conceptually universal (no tenant at all). The orchestrator does not derive tenant from the vehicle map or route cache; it uses `position.tenant_id` from the inbound MQTT event to scope the
   outbound occupancy topic.
4. **`OccupancyEvent` still carries `tenant_id`.** The event describes
   a _vehicle_, and the vehicle is tenant-scoped. The passengers named
   in `boarded_passenger_ids` / `alighted_passenger_ids` are universal
   and may belong to any tenant or none. This asymmetry is intentional
   and is why `boarding_passenger_events.passenger_id` (FK → `users.id`)
   can reference a user outside the parent event's tenant.
5. **Cross-tenant trips are allowed and expected.** A passenger who
   boards tenant A's vehicle and alights at tenant A's stop may later
   board tenant B's vehicle. The global set handles this correctly
   because it is keyed by passenger ID alone, not by (passenger,
   tenant).

### Per-passenger record

```python
{
    "origin_sequence": int,     # RouteStop.sequence where the passenger boarded
    "dest_sequence": int,       # RouteStop.sequence where they will alight
    "distance_km": float,       # route distance origin→dest (sum of haversine legs between consecutive stops)
    "passenger_id": str | None, # real user ID (universal, not tenant-bound), or None if anonymous
}
```

### Function contract

```python
def make_rng(vehicle_id: str, arrival_sequence: int) -> random.Random:
    digest = hashlib.sha256(f"{vehicle_id}:{arrival_sequence}".encode()).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))
```

`SimulationParams` is a frozen dataclass with two fields:

```python
@dataclass(frozen=True)
class SimulationParams:
    crush_capacity_factor: float   # from CRUSH_CAPACITY_FACTOR
    revenue_per_km: float          # from REVENUE_PER_KM
```

```python
def simulate_passengers(
    state: VehicleArrivalState,
    current_sequence: int,          # arriving RouteStop.sequence
    stops: list[RouteStop],         # sorted by .sequence (Task 3.1 guarantees)
    seating_capacity: int,
    passenger_pool: Sequence[str],
    excluded_ids: AbstractSet[str],
    params: SimulationParams,       # crush_capacity_factor, revenue_per_km
    rng: random.Random,
) -> SimulationResult: ...

@dataclass
class SimulationResult:
    boardings: int
    alightings: int
    onboard: int                      # passengers on board after this stop
    revenue_delta: float
    boarded_ids: list[str]            # real IDs only
    alighted_ids: list[str]           # real IDs only
    passengers: list[dict]            # the updated passenger list
```

The function is **pure**: it never mutates `state`, never reads module-level
state, and returns a new passenger list. Everything it needs comes in as an
argument. The **orchestrator owns** the process-wide `_globally_on_board`
set, passes it in as `excluded_ids`, and updates it from the result (§3).

### Core principles

1. **Per-passenger state.** Every boarder is a discrete record with an origin and destination. Alightings are determined by `dest_sequence == current_sequence`, not by a random draw.
2. **Deterministic given a seed.** All randomness uses a `random.Random` seeded from `make_rng(vehicle_id, arrival_sequence)`: an int taken from a SHA-256 digest, which is stable across Python versions and distinct per arrival.
3. **Real-ID assignment.** A random subset of new boarders receives a real `passenger_id` from the **universal** passenger pool (§7 "Universal passengers"). The remainder are anonymous (`passenger_id=None`).
4. **Global one-bus-at-a-time.** A real passenger cannot be assigned to two vehicles simultaneously. The orchestrator holds a single `_globally_on_board: set[str]` for the process and passes it to the engine as `excluded_ids`. IDs are released when passengers alight, when a vehicle changes route, and when a vehicle leaves the vehicle map. (See §12 for the restart caveat.)
5. **Revenue.** Each alighting passenger contributes `distance_km * REVENUE_PER_KM` to the event's `revenue_delta`. `REVENUE_PER_KM = 60.0` (matches the pre-existing constant).

### Order of operations at a stop

1. If `state.needs_synthesis`, synthesise anonymous passengers (below).
2. Alight passengers (rules below); accumulate revenue and collect real IDs.
3. Board new passengers (rules below).
4. Assign real IDs to a subset of the _new_ boarders.
5. Return the result; the caller applies it.

### Synthesising seeded passengers

When the state has `onboard > 0` but no passenger records (after a restart, or
after a route change), the engine creates `onboard` anonymous records at the
first arrival. Let `pos = index_of(stops, current_sequence)` be the array
position of the arriving stop (the cache guarantees sortedness, so this is
`bisect_left` over `sequence`):

- `origin_pos = randint(0, pos - 1)` if `pos > 0`, else `0`
- `dest_pos = randint(max(pos, 1), len(stops) - 1)`
- `origin_sequence = stops[origin_pos].sequence`
- `dest_sequence = stops[dest_pos].sequence`
- `distance_km` computed from origin to dest

**Sampling is over array positions, then mapped to `sequence` via
`stops[pos].sequence`.** This keeps the ranges valid for gapped sequence data
(e.g. `[0, 1, 3]`). Do not sample `sequence` values directly — the range
boundaries would be wrong.

Nobody synthesised can have a destination behind the bus, so `onboard` cannot
grow without bound. After this step `onboard == len(passengers)`.

### Boarding rules at a stop

- **Terminus (array position 0, when `len(stops) > 1`):**
  - `target = randint(int(capacity * 0.75), int(capacity * 1.10))`
  - `boarded = max(0, min(target, crush_capacity - current_onboard))`
  - Each boarder gets `dest_pos = randint(1, len(stops) - 1)` and
    `dest_sequence = stops[dest_pos].sequence`.
- **Mid-route (not first, not last position, `available_seats > 0`):**
  - `board_cap = max(1, capacity // 6)`
  - `boarded = randint(min(board_cap // 2, available_seats), min(board_cap, available_seats))`
  - Each boarder gets `dest_pos = randint(pos + 1, len(stops) - 1)` and
    `dest_sequence = stops[dest_pos].sequence` (sample positions, map to
    sequence — see the synthesis note above for why).
- **Last stop:** no new boardings, other than the through-passenger re-boardings below.

`current_onboard` and `available_seats` are measured **after** this stop's
alightings. `crush_capacity = int(seating_capacity * CRUSH_CAPACITY_FACTOR)` with `CRUSH_CAPACITY_FACTOR = 1.15` — matching the constant already in `passenger_simulation.py` (see §11 #5).

### Alighting rules at a stop

- **Non-last stops:** every passenger with `dest_sequence == current_sequence` alights. Revenue added.
- **Last stop, `len(stops) > 2`:** **everyone alights** — revenue is added for
  all, and every real ID goes into `alighted_ids` and is released from the
  global set. Then `k = min(randint(3, 6), alighted_count)` of the alighted
  passengers are **re-boarded as anonymous through-passengers**:
  `passenger_id = None`, `origin_pos = 0`, `origin_sequence = stops[0].sequence`,
  `dest_pos = randint(1, len(stops) - 1)`,
  `dest_sequence = stops[dest_pos].sequence`, new `distance_km`. They count in
  this event's `boardings` and (as alighters) in `alightings`, so
  `onboard = onboard_before − alightings + boardings` still holds and the next
  loop starts populated — preserving the legacy demo behaviour where the bus
  does not run empty after each loop.z
- **Last stop,** `len(stops) <= 2`**:** all alight; no through-passengers.

Through-passengers lose their identity at the loop boundary (§12). Their real
board→alight trip is fully recorded, and their real ID does not stay stuck in
the global set.

### Real-ID assignment

After computing the set of new boarders (through-passengers are always anonymous):

```text
excluded = (
    {p["passenger_id"] for p in remaining_passengers if p["passenger_id"]}
    | set(alighted_ids)              # no same-stop reboard
    | excluded_ids                   # global set: no double-booking
)
available = [pid for pid in passenger_pool if pid not in excluded]
n = min(len(new_boarders), len(available))
selected = rng.sample(available, n)   # random subset, assigned to the first n boarders
```

The orchestrator then updates `_globally_on_board`: remove `alighted_ids`, add
`boarded_ids`. The pool comes from a **single universal cached fetcher**
(`GET /api/v1/passengers` — no `tenant_id`, refreshed on the
same `VEHICLE_REFRESH_INTERVAL` as the vehicle map) and is passed into the
engine as an argument; it is not copied into per-vehicle or per-tenant state.
The exclusion set `excluded_ids` is process-global and is _not_ reset per
tenant — see "Universal passengers" above.

### Revenue

Every alighting, with a `passenger_id` or without, contributes `distance_km * REVENUE_PER_KM` (60.0 is the pre-existing constant; the design treats it as a simulation parameter, not a real currency value). The total per-stop is carried in the wire event as `revenue_delta`. The backend accumulates it into `analytics_daily.revenue` (existing `upsert_daily_analytics` handles this today; the backend consumer in Phase 7 just calls it).

### Testability

- Seed from `make_rng(vehicle_id, arrival_sequence)`.
- The simulation function is pure (signature above), so every constraint is testable in isolation: `alightings <= onboard_before`, `boardings <= crush headroom` (plus through-passengers at the last stop), `onboard == len(passengers)`, exclusions respected, revenue equals `sum(distance_km of alighters) * revenue_per_km`.
- The cross-vehicle uniqueness of real IDs is a property of the _orchestrator + global set_ and is tested there (two vehicles, one shared set).

---

## 8. Backend Consumption Design

### Subscription

The backend adds a second MQTT subscription: `gps/+/+/occupancy`, handled by
a new subscriber parallel to the existing `gps/+/+/position` subscriber. Each
subscriber validates against its own Pydantic schema and hands off to its own
async DB writer via `asyncio.run_coroutine_threadsafe`, matching the existing
`GPSMQTTSubscriber` pattern.

### Data model changes

Three table writes per occupancy event (in one transaction), plus a possible capacity-alert row (see §9):

1.  **Append-only aggregate log** — new table `occupancy_events`:

         id                  UUID PK
         tenant_id           UUID FK -> tenants.id   ON DELETE RESTRICT
         vehicle_id          UUID FK -> vehicles.id  ON DELETE RESTRICT
         stop_id             VARCHAR
         route_id            VARCHAR
         arrival_sequence    INTEGER NOT NULL
         boardings           INTEGER
         alightings          INTEGER
         onboard             INTEGER
         idempotency_key     VARCHAR UNIQUE
         position_timestamp  TIMESTAMPTZ
         service_timestamp   TIMESTAMPTZ
         revenue_delta       NUMERIC(10,2) NOT NULL DEFAULT 0
         created_at          TIMESTAMPTZ DEFAULT now()

    Indexes: `UNIQUE(idempotency_key)`; `(vehicle_id, arrival_sequence)` for the latest-sequence query (§4); `(tenant_id, position_timestamp)` for
    time-range queries.
    The `idempotency_key` UNIQUE constraint is what makes ingestion idempotent.

Insert uses `INSERT ... ON CONFLICT (idempotency_key) DO NOTHING`.

`source` from the wire payload is validated but **not** written to a
column — it is constant and adds no analytical value. If multi-publisher
provenance is ever needed, add a `source` column then.

2.  **Append-only per-passenger child log** — new table `boarding_passenger_events`:

         id                  UUID PK
         occupancy_event_id  UUID FK -> occupancy_events.id (ON DELETE CASCADE)
         passenger_id        UUID FK -> users.id     ON DELETE SET NULL
                             -- nullable; a deleted user must not delete the
                             -- audit row. Column type must match users.id.
         event_type          ENUM('boarded', 'alighted')
         created_at          TIMESTAMPTZ DEFAULT now()

    One row per real passenger per direction, derived from the event's `boarded_passenger_ids` / `alighted_passenger_ids`. Rows are inserted in the same transaction as the parent and only when the parent insert actually inserted, so duplicate events cause no duplicate children (the parent insert is the guard).

    > (`tenants.id`, `vehicles.id`, `users.id`). Confirm against the existing
    > SQLAlchemy models before writing the Alembic migration — do not assume
    > UUID vs. VARCHAR. `ON DELETE RESTRICT` on tenant/vehicle preserves the
    > audit log; `ON DELETE SET NULL` on passenger preserves the row when a
    > user is deleted.

3.  **Materialized current occupancy + revenue** — update
    `vehicles.current_occupancy = event.onboard`, `vehicles.updated_at = now()`;
    if `event.revenue_delta > 0`, `UPSERT analytics_daily ... revenue += event.revenue_delta` via the existing `upsert_daily_analytics`.

> **FK types (all three tables).** All FK column types must match the
> referenced PK types (`tenants.id`, `vehicles.id`, `users.id`). Confirm
> against the existing SQLAlchemy models before writing the Alembic
> migration — do not assume UUID vs. VARCHAR. `ON DELETE RESTRICT` on
> tenant/vehicle preserves the audit log; `ON DELETE SET NULL` on passenger
> preserves the row when a user is deleted.

### Transaction boundary

All three writes happen in a single transaction. If the aggregate insert conflicts (duplicate delivery), the child insert, the `vehicles` update, the revenue update **and the capacity alert** are all skipped. Assumption: the first delivery already committed (and alerted). This avoids the pathological case where a duplicate arrives after newer events and clobbers `current_occupancy` with a stale value, double-counts revenue, or re-fires an alert.

### Failure handling

- **Validation error** (Pydantic): log at ERROR, drop. Do not retry — the
  message is malformed, retrying won't help.
- **DB error** (transient): log at ERROR, drop. MQTT QoS 1 will not
  redeliver to a subscriber that already ACKed. If retry is needed later,
  add a dead-letter queue; out of scope for v1.
- **Unknown vehicle/tenant**: log at WARNING, drop. Do not auto-create;
  the simulator and the backend must agree on the fleet.

### WebSocket broadcast

After a successful commit (not after a duplicate that was skipped), broadcast
the existing `vehicle_occupancy_updated` message (unchanged from the current
backend's shape) via `manager.publish_to_tenant(...)`, so the frontend's
occupancy indicator and "X/Y seats" display continue to work without
modification:

    {
      "type": "vehicle_occupancy_updated",
      "vehicleId": ...,
      "currentOccupancy": ...,
      "seatingCapacity": ...,
      "remainingSeats": ...
    }

`remainingSeats = max(0, seatingCapacity - currentOccupancy)`.

---

## 9. Alert Behavior

The backend currently runs `SELECT ... FROM alerts WHERE type = 'delay' ...`
per vehicle. Reading the code shows this is triggered from
`backend/app/services/route_tracking_service.py` when position updates are
processed — it is a _consumer_ of position events, not a simulator.

**Decision: delay alerts stay in the backend. Not in scope for passenger_service.**

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
one; if the type is a DB enum, the migration is part of the occupancy-service
task). When the backend processes an **inserted** (non-duplicate) occupancy
event with `onboard >= seating_capacity * CAPACITY_ALERT_THRESHOLD`, it emits
a capacity alert, deduplicated per `(vehicle_id, type='capacity')` for
`CAPACITY_ALERT_DEDUP_SECONDS` of the most recent alert. This is a small
addition to the existing alert service, not a new subsystem.

Constants, kept next to the existing alert thresholds:

| Constant                       | Value | Notes                                                    |
| ------------------------------ | ----- | -------------------------------------------------------- |
| `CAPACITY_ALERT_THRESHOLD`     | 0.9   | Softer, earlier trigger.                                 |
| `CAPACITY_ALERT_DEDUP_SECONDS` | 300   | 5-minute dedup window per vehicle.                       |
| `CRUSH_CAPACITY_FACTOR`        | 1.15  | Hard ceiling used by the simulation (passenger_service). |

---

## 10. Backend Deletion Plan

**Before deleting anything, the following must be verified by reading the
actual code and listing each function/class/module with file path. The list
below is derived from the design phase's read of the repo; confirm before
removing.**

### Cutover order (avoids double writes)

The legacy simulation and the new pipeline both write `vehicles.current_occupancy`
and `analytics_daily.revenue`. They must never both be live:

1. Build and test the new consumer (subscriber, service, broadcast) with the subscriber **not yet registered**.
2. **Disable the legacy simulation loop** (flag or removal of its scheduler).
3. **Register the occupancy subscriber** in the app lifespan.
4. Run the verification checklist below.
5. Only then delete the legacy code.

### To delete (simulation code made redundant by passenger_service)

| Path                                                                         | What it does                                                                                 | Delete after                                                                                                                                                                                                  |
| ---------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `backend/app/services/passenger_simulation.py`                               | The whole module: generated boardings/alightings per stop                                    | Cutover step 4 passes                                                                                                                                                                                         |
| `backend/app/services/boarding_service.py`                                   | `record_single_boarding` / `record_stop_events` — writes the legacy `boarding_records` table | Same, **after** the Task 8.1 equivalence check: for a sampled vehicle+stop, boardings/alightings counts in `boarding_records` and in `boarding_passenger_events` agree over the same `arrival_sequence` range |
| `backend/app/models/boarding_record.py`                                      | The legacy aggregate model                                                                   | After `occupancy_events` and `boarding_passenger_events` are live                                                                                                                                             |
| `boarding_records` table (migration)                                         | Drop the legacy table, `boarding_event_type_enum`, and `idx_boarding_*` indexes              | Same                                                                                                                                                                                                          |
| Any scheduled task / background loop that calls into `passenger_simulation`  | Whatever drove the simulation tick                                                           | Disabled at cutover step 2; removed with the module                                                                                                                                                           |
| `backend/tests/test_passenger_simulation.py` and any `test_boarding_*` tests | Tests for the above                                                                          | Same as above                                                                                                                                                                                                 |

### To keep (not simulation)

| Path                                                       | Why it stays                                                                                                                                         |
| ---------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `backend/app/services/route_tracking_service.py`           | Delay detection — business rule, consumes position events, not a simulator                                                                           |
| `backend/app/services/alert_service.py` (or equivalent)    | Alert generation, dedup, acknowledge — business logic                                                                                                |
| `backend/app/services/gps_mqtt_subscriber.py`              | Existing position consumer — extended, not replaced                                                                                                  |
| All vehicle/route/stop CRUD                                | Data ownership, not simulation                                                                                                                       |
| `backend/app/crud/analytics.py` (`upsert_daily_analytics`) | Revenue accumulation — called by the new occupancy consumer                                                                                          |
| `trips` table and model                                    | **Vestigial in v1.** No new rows written after Phase 8. Kept for the eventual "trip lifecycle" feature. Add a comment in the model file noting this. |

### Loop counting — disclaimer

`gps_service` does **not** implement loop counting today. After Phase 8,
nothing in the system updates `planned_loops` / `completed_loops` (if the legacy
simulation currently writes them, those writes stop with the module). Loop
counting is a position concern and is therefore a **`gps_service` follow-up**,
not a `passenger_service` or backend task. Until it is built, those fields will
be stale or unset. This is accepted for v1 and is recorded in §11 #3 and §12 and
in the architecture docs.

### The new code to add (not a deletion, but part of the same change)

- `backend/app/services/occupancy_mqtt_subscriber.py` — new subscriber
- `backend/app/services/occupancy_service.py` — writes to `occupancy_events` and `boarding_passenger_events`,
  updates `vehicles.current_occupancy`, accumulates revenue, triggers capacity alerts, broadcasts over WebSocket
- `backend/app/schemas/occupancy.py` — `OccupancyEvent` Pydantic model
- `backend/app/models/occupancy_event.py` and `backend/app/models/boarding_passenger_event.py` — SQLAlchemy models
- Alembic migration for `occupancy_events` and `boarding_passenger_events`
- Two new REST endpoints: `latest-arrival-sequence` and `passengers`

### Verification that nothing broke

After cutover:

1. Run `docker compose up --build`.
2. Wait for one full route loop (a few minutes with the demo's tick interval).
3. Query: `SELECT COUNT(*) FROM occupancy_events;` — should be growing.
4. Query: `SELECT COUNT(*) FROM boarding_passenger_events;` — should be growing (real-ID rows).
5. Query: `SELECT vehicle_id, current_occupancy FROM vehicles;` — should
   show plausible non-zero values for active vehicles.
6. Check `analytics_daily.revenue` grows once per stop, not twice (legacy writer really is off).
7. Frontend: occupancy indicator on the map should update live.
8. After deletion, confirm no legacy references remain:
   `rg "passenger_simulation|boarding_records" backend/ --glob '!**/alembic/versions/**'`.

---

## 11. Open Questions

Items marked (resolved) are kept for the decision record; only the
unmarked rows are open.

| #   | Question                                                                 | Recommended default                                                                                                                                                                                                                                                                                       | Impact if wrong                    |
| --- | ------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------- |
| 1   | Should `arrival_sequence` be seeded from the backend?                    | **Resolved: yes**, lazily on a vehicle's first appearance. Backend exposes `GET /api/v1/service/vehicles/{id}/latest-arrival-sequence`.                                                                                                                                                                   | —                                  |
| 2   | Should `onboard` be seeded from `vehicles.current_occupancy`?            | **Resolved: yes**, from `currentOccupancy` in the vehicle-list fetch, with anonymous passengers synthesised on the first arrival (§5, §7).                                                                                                                                                                | —                                  |
| 3   | Is loop counting (`completed_loops`) simulation or derived?              | **Open — gps_service concern.** gps_service has no loop counting today; recorded as a disclaimer (§10, §12). Not part of this project.                                                                                                                                                                    | Low — cosmetic; not demo-critical. |
| 4   | Should the audit log be partitioned or pruned (it grows forever)?        | **Defer.** Demo scale doesn't need it.                                                                                                                                                                                                                                                                    | Low.                               |
| 5   | _(resolved)_ Should `onboard` be allowed to exceed `seating_capacity`?   | **Yes, up to `CRUSH_CAPACITY_FACTOR * seating_capacity`** (1.15 × 45 = 51 max for default). Only reachable at terminus.                                                                                                                                                                                   | —                                  |
| 6   | _(resolved)_ Two stops near-simultaneous arrival?                        | **Only fire one arrival per position event** (first match in route order).                                                                                                                                                                                                                                | —                                  |
| 7   | _(resolved)_ Determinism of the RNG across Python versions.              | **Seed = int from `sha256(f"{vehicle_id}:{arrival_sequence}")`** via `make_rng`.                                                                                                                                                                                                                          | —                                  |
| 8   | Should `passenger_service` expose a REST API beyond health/status?       | **No.** Debug via `/status` only.                                                                                                                                                                                                                                                                         | Low.                               |
| 9   | What happens if the position stream stalls (all vehicles stop moving)?   | **Service idles; no events fire.** Health endpoint stays green.                                                                                                                                                                                                                                           | Low.                               |
| 10  | Should the backend reject occupancy events for vehicles it doesn't know? | **Yes.** Log warning, drop. Never auto-create.                                                                                                                                                                                                                                                            | Low.                               |
| 11  | Global "one bus at a time" invariant on restart.                         | **`_globally_on_board` is not reseeded on restart** (v1). A restart can theoretically double-book a passenger; self-corrects on next alighting. Documented in §12.                                                                                                                                        | Low at demo scale.                 |
| 12  | Where do passenger IDs come from?                                        | **Resolved: the backend's existing passengers endpoint** (`GET /api/v1/passengers`), called **without** `tenant_id` — passengers are universal (§7). One process-wide cached fetcher, refreshed on the vehicle-map interval, passed to the engine. Do not add a second endpoint; do not pass `tenant_id`. | —                                  |
| 13  | Revenue currency and rate.                                               | `REVENUE_PER_KM = 60.0`, carried as `revenue_delta: float` on the event. Backend accumulates to `analytics_daily.revenue`. Matches existing behaviour.                                                                                                                                                    | Low.                               |

---

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

- **Publish failure loses the event.** If the MQTT publish fails after its
  retries, the event is logged and dropped while the in-memory state has already
  advanced. The next event's `onboard` is self-consistent but the backend misses
  one step.

### Data consistency

- **Occupancy and vehicle state can drift on partial failure.** The
  backend writes to `occupancy_events` and updates
  `vehicles.current_occupancy` in one transaction, so within a single
  event they stay consistent. But if a downstream consumer (e.g. the
  frontend) reads them at different moments, it may observe a mismatch
  for up to one event's processing time.

- **Restart visibility.** Even with seeding, a restart is visible: the
  first post-restart occupancy event's `service_timestamp` lags the
  triggering `position_timestamp` by the restart duration. Consumers
  correlating the two timestamps should tolerate gaps.

- **Consumer drops on DB error.** The backend does not retry a transient DB
  failure (§8), so delivery is not end-to-end at-least-once in v1.

- **Clock skew.** Timestamps are UTC and assume NTP-synced hosts. A
  significant skew between `gps_service` and `passenger_service` will
  make `service_timestamp − position_timestamp` unreliable, though
  ordering within a service is preserved.

- **Restart may double-fire a stop arrival.** If a vehicle is at a stop
  when `passenger_service` crashes and is still there at restart, the
  arrival fires once more after seeding (with `arrival_sequence + 1`).
  The idempotency key differs, so both rows persist. Cosmetic at demo
  scale. To fix: seed `last_stop_id` and `last_arrival_ts` alongside
  `arrival_sequence` (deferred — see §6).

### Passenger tracking

- **Global "one bus" invariant is not restart-safe.** `_globally_on_board`
  is a process-local set owned by the orchestrator. After a crash and
  restart, a real passenger who was mid-trip can theoretically be assigned
  to a second bus; their old trip's alighting is never recorded, because the
  passengers on board are re-synthesised anonymously. The window is bounded by
  one route loop. Documented for demo-scale deployment; a production system
  would persist this set (Redis) or derive it from the latest per-passenger
  rows in `boarding_passenger_events`.
- **Passengers are universal, not tenant-bound.** A real passenger ID may
  appear on vehicles of different tenants across the day; the global set
  (§7 "Universal passengers") enforces the one-bus-at-a-time rule across
  _all_ tenants in the process, not per tenant. This is correct and
  intended. It also means the "latest per-passenger row" recovery option
  above is _tenant-agnostic_ — `boarding_passenger_events` is the global
  record of every real passenger's last boarded/alighted event, regardless
  of which tenant's vehicle they were on.
- **Cross-tenant FK asymmetry (intentional).** `occupancy_events.tenant_id`
  is tenant-scoped (it describes a vehicle), while
  `boarding_passenger_events.passenger_id` references a universal user.
  A `boarding_passenger_events` row can therefore point at a user outside
  the parent event's tenant. This is not a bug — it is the schema
  reflecting reality. Do not "fix" it by adding a `tenant_id` to the
  child table.

- **Synthesised passengers are anonymous.** After a restart or a route
  change, the `onboard` passengers are re-created without real identities
  and with random destinations; their individual trips are not attributed.

- **Through-passenger identity is dropped at the loop boundary.** At the last
  stop every passenger alights (real IDs recorded and released), and 3–6 of
  them re-board anonymously for the next leg. The next leg's alightings cannot
  be correlated back to the same user.

- **Route change mid-day** drops the passenger list for that vehicle and
  re-synthesises it for the new route's stops; real IDs are released.

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

- **Loop routes with coincident ends.** If the first and last stop of a
  route are the same physical location (or within `STOP_ARRIVAL_RADIUS_M`),
  the detector's "first match in route order" rule fires the _origin_
  stop on every return to the terminus, never the last stop. The
  simulation's last-stop branch (all alight + 3–6 anonymous re-boards)
  then never runs, and `onboard` drifts. **Verify seed data does not
  place the terminus and origin within the radius.** Handling this
  properly needs a heading/direction input — out of scope for v1.

- **No handling for two stops within detection radius.** The detector
  returns the first match in route order, not the nearest; if two stops are
  within 30m, the one appearing first in the route's stop list wins. Verify
  seed data does not place stops this close.

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

### Loop counting

- **No loop counting anywhere after Phase 8.** `gps_service` does not
  implement loop counting today, and the legacy simulation is removed.
  `planned_loops` / `completed_loops` will be stale or unset until
  `gps_service` gains this feature (see §10). No UI in v1 may display them as live values.

### Trips

- **No trip lifecycle in v1.** Arrivals are a per-vehicle sequence, not grouped into trips. The `trips` table exists in the schema but receives no new rows after Phase 8. Historical "trip" views would need to derive groupings from `arrival_sequence` + timestamps. Adding a proper trip lifecycle is a future feature (`state.current_trip_id` is threaded through but stays `None` in v1).
