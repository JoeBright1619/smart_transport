# API Spec — Analytics

## `GET /api/v1/analytics`
**Roles:** `admin`, `operator`
**Query params:** `?from=2026-04-01&to=2026-04-08`

- Default range: last 7 days
- Maximum range: 90 days
- Dates are inclusive, format `YYYY-MM-DD`

**Response `200`:**
```json
{
  "data": {
    "summary": {
      "totalTrips": 148,
      "onTimePercentage": 91.2,
      "avgDelay": 3.3,
      "totalPassengers": 5920,
      "totalRevenue": 2960000,
      "totalFuelConsumption": 850
    },
    "daily": [
      {
        "date": "2026-04-01",
        "totalTrips": 21,
        "onTimePercentage": 90.0,
        "avgDelay": 3.5,
        "totalPassengers": 840,
        "fuelConsumption": 122,
        "revenue": 420000
      },
      {
        "date": "2026-04-02",
        "totalTrips": 19,
        "onTimePercentage": 94.7,
        "avgDelay": 2.1,
        "totalPassengers": 760,
        "fuelConsumption": 109,
        "revenue": 380000
      }
    ]
  },
  "meta": null
}
```

**Notes:**
- `revenue` is in the tenant's local currency (RWF by default)
- `fuelConsumption` is in litres
- `onTimePercentage` is a float rounded to 1 decimal place
- `avgDelay` is average delay in minutes (float)
- Results are pre-aggregated from the `analytics` table; not computed on the fly
- Cache TTL: 60 seconds (Redis, keyed by `tenant_id + date range`)
