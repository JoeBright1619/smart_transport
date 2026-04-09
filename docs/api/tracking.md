# API Spec — Arrival Time Estimation & WebSocket Tracking

---

## `GET /api/v1/arrivals`
**Roles:** All authenticated (including `passenger`)
**Query params:** `?stopId=stop-uuid` *(required)*

Returns all active vehicles approaching the specified stop with estimated arrival time.

**Response `200`:**
```json
{
  "data": [
    {
      "vehicleId": "veh-uuid",
      "registrationNumber": "RAD 001 A",
      "routeId": "route-uuid",
      "routeName": "Nyabugogo - Kimironko",
      "distanceToStopKm": 2.4,
      "currentSpeedKmh": 35,
      "etaMinutes": 4,
      "estimatedArrivalTime": "2026-04-08T17:04:00Z",
      "status": "active"
    },
    {
      "vehicleId": "veh-uuid-2",
      "registrationNumber": "RAD 003 C",
      "routeName": "Nyabugogo - Kimironko",
      "distanceToStopKm": 0.0,
      "currentSpeedKmh": 0,
      "etaMinutes": null,
      "estimatedArrivalTime": null,
      "status": "stopped"
    }
  ],
  "meta": null
}
```

**Calculation:**
```
distance_km  = haversine(vehicle.lat, vehicle.lng, stop.lat, stop.lng)
eta_minutes  = round((distance_km / vehicle.speed_kmh) * 60)
arrival_time = now_utc + eta_minutes
```

**Edge cases:**
| Condition | Behaviour |
|---|---|
| `vehicle.speed == 0` | `status: "stopped"`, `etaMinutes: null`, `estimatedArrivalTime: null` |
| Vehicle not on a route that serves this stop | Excluded from results |
| Vehicle `status != "active"` | Excluded from results |
| Stop does not serve any active route | Returns empty `data: []` |

**Errors:** `404` if `stopId` not found or belongs to another tenant | `400` if `stopId` param missing.

---

## WebSocket — `WS /ws/tracking`

**URL:** `ws://host/ws/tracking?token=<access_token>`

Authenticated WebSocket for live vehicle position updates, scoped to the authenticated user's tenant.

### Connection
- Authenticate via `?token=<jwt>` query parameter
- Server validates JWT on connection. Rejects with `code: 4001` if token is invalid or missing.
- Only vehicles belonging to the authenticated user's **tenant** are broadcast — never cross-tenant data.

### Message Format (server → client)
Broadcast every **5 seconds**:
```json
{
  "type": "vehicle_update",
  "data": [
    {
      "vehicleId": "veh-uuid",
      "lat": -1.9450,
      "lng": 30.0907,
      "speed": 35,
      "heading": 90,
      "fuel": 74,
      "engineStatus": "good",
      "timestamp": "2026-04-08T17:00:05Z"
    }
  ]
}
```

### Redis Channel
Each tenant's vehicle updates flow through a dedicated Redis pub/sub channel:
```
vehicle_updates:{tenant_id}
```
Example: `vehicle_updates:ten-demo-001`

The `ConnectionManager` broadcasts only to WebSocket clients whose `tenant_id` matches the channel.
