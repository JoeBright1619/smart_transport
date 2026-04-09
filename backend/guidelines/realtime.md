# Backend — Real-Time Tracking (WebSocket + Redis)

> Rules for the WebSocket server and Redis pub/sub used for live vehicle position broadcasting.

---

## Architecture

```
GPS Feed / Backend Simulation (per tenant)
        │
        ▼
  AlertService.evaluate(tenant_id)  ← runs on each position update
        │
        ▼
  PostgreSQL  ← persist alert if triggered
        │
        ▼
  Redis Pub/Sub — tenant-scoped channel
  Channel: "vehicle_updates:{tenant_id}"    e.g.  vehicle_updates:ten-abc123
        │
        ▼
  ConnectionManager
  (tracks tenant_id per connected WebSocket client)
        │  → broadcasts ONLY to clients matching tenant_id
        ▼
  React Frontend — updates map markers for this tenant's vehicles only
```

---

## WebSocket Endpoint

- **URL:** `ws://host/ws/tracking?token=<jwt>`
- Authenticate via query-param JWT — reject and disconnect unauthorized clients immediately
- Do not broadcast any data to unauthenticated connections

---

## Tenant-Scoped Channels (Critical)

Redis channels **must** be scoped per tenant:

```
vehicle_updates:{tenant_id}
```

**Never** use a single shared `vehicle_updates` channel — it would broadcast all tenants' vehicle positions to all clients, which is a data isolation violation.

`superadmin` role may subscribe to `vehicle_updates:all` for platform monitoring (disabled in the prototype phase).

---

## ConnectionManager Rules

The `ConnectionManager` class in `websocket/manager.py` must:
- Store `(websocket, tenant_id)` pairs — not just websockets
- On `broadcast()`, filter connections to only those matching the `tenant_id` of the publisher
- Subscribe to `vehicle_updates:{tenant_id}` on Redis, fan-out only to same-tenant clients

---

## Message Format

```json
{
  "type": "vehicle_update",
  "data": [
    {
      "vehicleId": "veh-1",
      "lat": -1.9450,
      "lng": 30.0907,
      "speed": 35,
      "heading": 90,
      "timestamp": "2026-03-24T12:00:00Z"
    }
  ]
}
```

- Position updates broadcast every **5 seconds**
- Coordinates in WGS84 decimal degrees. Speed in km/h. Heading in degrees 0–360.

---

## Performance

- Use Redis pub/sub (not polling) for fan-out across multiple backend instances
- The `ConnectionManager` should handle connect/disconnect gracefully without crashing the broadcast loop
- Use `asyncio` for all WebSocket handling — never block the event loop
