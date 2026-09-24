# GPS Service

A standalone service that simulates GPS data from vehicles using MQTT for efficient, reliable communication. Designed to mimic real GPS hardware and can be easily swapped with real GPS device integration.

## Purpose

This service generates realistic GPS data (position, speed, heading, fuel) for vehicles and publishes it to an MQTT broker. It mimics how actual GPS tracking devices work in production and supports industry-standard MQTT communication protocols.

## Why External?

- **Separation of concerns**: GPS generation is independent from core business logic
- **Production-ready**: Easy to replace with real GPS hardware or third-party service
- **Efficient**: MQTT is the industry standard for IoT/GPS communication
- **Reliable**: Built-in QoS levels ensure no dropped GPS updates
- **Scalable**: Can run on separate infrastructure
- **Testable**: Can test GPS → Backend integration separately

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
python -m gps_service.main

# Or with custom config
GPS_SERVICE_PORT=8081 python -m gps_service.main
```

## Configuration

See `config.py` for all configuration options:

| Variable | Description | Default |
|----------|-------------|---------|
| `MQTT_BROKER_URL` | MQTT broker URL | localhost |
| `MQTT_BROKER_PORT` | MQTT broker port | 1883 |
| `MQTT_TOPIC_PREFIX` | Topic prefix for GPS data | gps |
| `MQTT_USERNAME` | MQTT username (optional) | None |
| `MQTT_PASSWORD` | MQTT password (optional) | None |
| `GPS_SERVICE_PORT` | Port to run the service on | 8080 |
| `POLL_INTERVAL_SECONDS` | How often to send updates | 5 |
| `SIMULATION_MODE` | true=simulated, false=real GPS | true |
| `RETRY_ATTEMPTS` | MQTT publish retry attempts | 3 |
| `QOS_LEVEL` | MQTT Quality of Service level | 1 |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      GPS Service                            │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌──────────────┐    ┌───────────────┐ │
│  │  Vehicle    │    │   Position   │    │    MQTT       │ │
│  │  Manager    │───▶│  Calculator  │───▶│   Publisher   │ │
│  └─────────────┘    └──────────────┘    └───────────────┘ │
│         │                                       │          │
│         ▼                                       ▼          │
│  ┌─────────────┐                      ┌───────────────┐   │
│  │   Route     │                      │   MQTT        │   │
│  │  Follower   │                      │   Broker      │   │
│  └─────────────┘                      │  (Redis/Mosquitto)│
│                                        └───────────────┘   │
│                                                      │     │
│                                                      ▼     │
│                                        ┌─────────────────────┐
│                                        │      Backend        │
│                                        │  (Subscribes to GPS)│
│                                        └─────────────────────┘
└─────────────────────────────────────────────────────────────┘
```

## MQTT Topic Structure

GPS data is published to topics following this pattern:

```
{prefix}/{tenant_id}/{vehicle_id}/position
```

### Example Topics

```
# Published messages
gps/tenant-123/veh-001/position
gps/tenant-123/veh-002/position

# Backend subscribes to
gps/+/+/position   # All tenants, all vehicles
gps/tenant-123/#   # Specific tenant, all vehicles
```

## Data Format

### Outgoing to Backend (MQTT Payload)

```json
{
  "vehicle_id": "veh-123",
  "registration_number": "RAD 001 A",
  "lat": -1.9536,
  "lng": 30.0606,
  "speed": 35,
  "heading": 90,
  "fuel": 75,
  "engine_status": "good",
  "timestamp": "2026-09-18T17:56:15Z",
  "source": "gps_service",
  "device_id": "gps-sim-001",
  "tenant_id": "tenant-123"
}
```

### MQTT QoS Levels

| Level | Delivery Guarantee | Use Case |
|-------|-------------------|----------|
| 0 | At most once (fire and forget) | High-frequency, low-criticality |
| 1 | At least once (with retry) | Standard GPS tracking (default) |
| 2 | Exactly once | Critical tracking, billing |

### Retained Messages

GPS positions can be published as "retained" messages, allowing new subscribers to immediately receive the last known position.

## API Endpoints

The GPS service exposes its own API for monitoring and control:

- `GET /health` - Health check
- `GET /status` - Service status with MQTT connection info
- `GET /vehicles` - List vehicles being tracked
- `POST /vehicles` - Add a vehicle to track
- `DELETE /vehicles/{vehicle_id}` - Remove a vehicle

## Switching to Real GPS

When ready for production with real GPS hardware:

1. **Disable simulation mode**: `SIMULATION_MODE=false`
2. **Configure MQTT broker** to accept real device connections
3. **Update topic pattern** if real devices use different topics
4. The service can:
   - Act as a bridge between real devices and backend
   - Or real devices publish directly to the MQTT broker

## Requirements

- Python 3.11+
- paho-mqtt (MQTT client)
- pydantic (data validation)
- See requirements.txt for full list

## MQTT Broker Options

This service works with any MQTT v3.1/v5.0 compliant broker:

| Broker | Notes |
|--------|-------|
| **Redis** | Built-in Pub/Sub, great if already using Redis |
| **Mosquitto** | Lightweight, open-source |
| **EMQX** | Enterprise-grade, high scalability |
| **AWS IoT Core** | If deploying on AWS |
| **Azure IoT Hub** | If deploying on Azure |

## Example Docker Compose

```yaml
version: '3.8'
services:
  gps-service:
    build: ./gps_service
    environment:
      - MQTT_BROKER_URL=mosquitto
      - MQTT_BROKER_PORT=1883
      - POLL_INTERVAL_SECONDS=5
    depends_on:
      - mosquitto

  mosquitto:
    image: eclipse-mosquitto:2
    ports:
      - "1883:1883"
    volumes:
      - ./mosquitto/config:/mosquitto/config
```
