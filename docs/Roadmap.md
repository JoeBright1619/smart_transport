# Product Roadmap

> **Purpose:** Separates MVP from future versions to prevent scope creep and communicate direction.
> MVP = v1.0. Post-MVP work begins only after v1.0 ships and is validated with real users.

---

## v1.0 — MVP (Current Target)

**Goal:** Working multi-tenant fleet management platform that a transport company can use from day one.

See [`MVP-Scope.md`](./MVP-Scope.md) for the full feature list and definition of done.

**Core capabilities:**
- Multi-tenant auth with JWT + role-based access
- Real-time vehicle tracking (WebSocket + Redis)
- Fleet, route, driver, and trip management
- Automated alerts
- Simple physics-based arrival time estimation
- Basic analytics dashboard (pro+ tier)
- Maintenance logging (pro+ tier)
- Superadmin portal for tenant management

---

## v1.1 — Monetization & Notifications

**Goal:** Make the platform self-sustaining — tenants can sign up and pay without manual superadmin intervention.

| Feature | Description |
|---|---|
| **Stripe / Flutterwave billing** | Subscription checkout, webhook-based tier upgrades/downgrades, invoice emails |
| **Self-serve trial → paid conversion** | In-app upgrade prompts when trial ends or limit hit |
| **Email alerts** | Route delay, vehicle breakdown, maintenance due — via SendGrid or Africa's Talking |
| **SMS alerts** | Critical alerts via Africa's Talking (Rwanda-native SMS gateway) |
| **Audit log viewer** | `/security` page showing the `audit_logs` table for tenant admins |
| **Driver performance reports** | Per-driver trip count, on-time rate, delay average |
| **Recurring trip schedules** | Auto-create daily trips from a schedule template |
| **Geofence drawing tool** | UI polygon editor for defining route corridors |

---

## v1.2 — Intelligence & Integrations

**Goal:** Make the platform smarter and integrate with the wider transport ecosystem.

| Feature | Description |
|---|---|
| **ML-based ETA predictions** | Historical speed + traffic patterns replace simple Haversine calculation |
| **GTFS data import** | Bulk import routes and stops from GTFS feeds (used by most African transport agencies) |
| **Historical route playback** | Replay a vehicle's GPS-tracked journey from a stored `position_history` table |
| **Enterprise API access** | API key management, rate limiting, developer portal for enterprise tier |
| **White-label branding** | Per-tenant custom logo, colour scheme, and subdomain |
| **Passenger mobile app** | React Native app for the `passenger` role — stop arrival times, live bus map |
| **PostGIS geofence queries** | Replace simple distance check with proper spatial query for geofence alerts |

---

## v2.0 — AI & Scale

**Goal:** Transform from a management tool into an intelligent transport intelligence platform.

| Feature | Description |
|---|---|
| **AI dispatch optimisation** | Suggest optimal vehicle-driver-route assignments based on demand and availability |
| **Predictive maintenance** | ML model trained on engine/fuel data to predict breakdowns before they happen |
| **Multi-city / multi-country** | Per-tenant geographic region settings; support for multiple currency + locale |
| **Public data API** | Anonymised urban mobility data sold to city planners and researchers |
| **Demand heatmaps** | Visualise passenger density by stop, time of day, and route |
| **Multi-language UI** | Kinyarwanda, French, Swahili in addition to English |
| **Mobile driver app** | Dedicated app for drivers: current trip, turn-by-turn route, passenger count input |
| **Offline-resilient tracking** | Local GPS buffering when mobile data is unavailable; sync on reconnect |

---

## Monetization Timeline

| Version | Revenue Source |
|---|---|
| v1.0 | Manual tenant creation; free demo; no billing yet |
| v1.1 | Stripe/Flutterwave subscriptions live; trial-to-paid conversion |
| v1.2 | Enterprise tier unlocked (API access, white-label); larger contract deals |
| v2.0 | Data monetization; government / city contracts (B2G) |

---

## Pricing Direction (Indicative)

| Tier | Price | Target Customer |
|---|---|---|
| Starter (≤20 vehicles) | $15 / vehicle / month | Small private operators |
| Pro (≤100 vehicles) | $12 / vehicle / month | Mid-size bus companies |
| Enterprise (unlimited) | Custom contract | City transport authorities, large fleets |

> These prices are indicative and should be validated with real customers before v1.1 ships.
> For Rwanda/East Africa, consider offering pricing in RWF to reduce currency risk for customers.
