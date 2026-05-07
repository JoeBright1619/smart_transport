from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from random import uniform
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import decode_access_token
from app.models.telemetry import Telemetry
from app.models.tenant import Tenant
from app.models.user import User
from app.models.vehicle import Vehicle
from app.websocket.manager import manager

router = APIRouter()
logger = logging.getLogger(__name__)

TRACKING_REJECT_CODE = 4001
BROADCAST_INTERVAL_SECONDS = 5

_broadcast_tasks: dict[str, asyncio.Task[None]] = {}
_broadcast_lock = asyncio.Lock()


async def _authenticate_tracking_connection(websocket: WebSocket) -> str | None:
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=TRACKING_REJECT_CODE)
        return None

    try:
        payload = decode_access_token(token)
    except JWTError:
        await websocket.close(code=TRACKING_REJECT_CODE)
        return None

    user_id = payload.get("userId")
    tenant_id = payload.get("tenantId")
    role = payload.get("role")
    if not user_id or not tenant_id or not role:
        await websocket.close(code=TRACKING_REJECT_CODE)
        return None

    async with AsyncSessionLocal() as db:
        user = await db.scalar(
            select(User).where(
                User.id == user_id,
                User.tenant_id == tenant_id,
                User.role == role,
                User.is_deleted.is_(False),
            )
        )
        tenant = await db.get(Tenant, tenant_id)

    if user is None or tenant is None or not tenant.is_active:
        await websocket.close(code=TRACKING_REJECT_CODE)
        return None

    return tenant_id


@router.websocket("/ws/tracking")
async def tracking_websocket(websocket: WebSocket) -> None:
    tenant_id = await _authenticate_tracking_connection(websocket)
    if tenant_id is None:
        return

    await manager.connect(websocket, tenant_id)
    await _ensure_broadcast_loop(tenant_id)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(websocket, tenant_id)
        await _stop_broadcast_loop_if_idle(tenant_id)


async def _ensure_broadcast_loop(tenant_id: str) -> None:
    async with _broadcast_lock:
        task = _broadcast_tasks.get(tenant_id)
        if task is not None and not task.done():
            return

        _broadcast_tasks[tenant_id] = asyncio.create_task(_broadcast_loop(tenant_id))


async def _stop_broadcast_loop_if_idle(tenant_id: str) -> None:
    async with _broadcast_lock:
        if manager.active_connections.get(tenant_id):
            return

        task = _broadcast_tasks.pop(tenant_id, None)
        if task is not None:
            task.cancel()


async def _broadcast_loop(tenant_id: str) -> None:
    try:
        while True:
            try:
                message = await _build_vehicle_update_message(tenant_id)
                await _publish_vehicle_update(tenant_id, message)
                await _simulate_vehicle_positions(tenant_id)
            except Exception:
                logger.warning(
                    "Vehicle tracking broadcast cycle failed for tenant %s",
                    tenant_id,
                    exc_info=True,
                )

            await asyncio.sleep(BROADCAST_INTERVAL_SECONDS)
    except asyncio.CancelledError:
        raise


async def _build_vehicle_update_message(tenant_id: str) -> dict[str, Any]:
    timestamp = datetime.now(timezone.utc)

    async with AsyncSessionLocal() as db:
        vehicles = (
            await db.scalars(
                select(Vehicle).where(
                    Vehicle.tenant_id == tenant_id,
                    Vehicle.is_deleted.is_(False),
                    Vehicle.status == "active",
                    Vehicle.lat.is_not(None),
                    Vehicle.lng.is_not(None),
                )
            )
        ).all()

        telemetry_rows = [
            Telemetry(
                tenant_id=tenant_id,
                vehicle_id=vehicle.id,
                lat=vehicle.lat,
                lng=vehicle.lng,
                speed=vehicle.speed or 0,
                heading=vehicle.heading or 0,
                timestamp=timestamp,
            )
            for vehicle in vehicles
        ]

        if telemetry_rows:
            db.add_all(telemetry_rows)
            try:
                await db.commit()
            except Exception:
                await db.rollback()
                logger.warning(
                    "Telemetry write failed for tenant %s",
                    tenant_id,
                    exc_info=True,
                )

        return {
            "type": "vehicle_update",
            "data": [
                {
                    "vehicleId": vehicle.id,
                    "lat": vehicle.lat,
                    "lng": vehicle.lng,
                    "speed": vehicle.speed or 0,
                    "heading": vehicle.heading or 0,
                    "fuel": vehicle.fuel,
                    "engineStatus": vehicle.engine_status,
                    "timestamp": timestamp.isoformat(),
                }
                for vehicle in vehicles
            ],
        }


async def _publish_vehicle_update(tenant_id: str, message: dict[str, Any]) -> None:
    await manager.publish_to_tenant(tenant_id, message)


async def _simulate_vehicle_positions(tenant_id: str) -> None:
    async with AsyncSessionLocal() as db:
        vehicles = (
            await db.scalars(
                select(Vehicle).where(
                    Vehicle.tenant_id == tenant_id,
                    Vehicle.is_deleted.is_(False),
                    Vehicle.status == "active",
                    Vehicle.lat.is_not(None),
                    Vehicle.lng.is_not(None),
                )
            )
        ).all()

        if not vehicles:
            return

        for vehicle in vehicles:
            vehicle.lat = (vehicle.lat or 0) + uniform(-0.0002, 0.0002)  # nosec B311
            vehicle.lng = (vehicle.lng or 0) + uniform(-0.0002, 0.0002)  # nosec B311
            vehicle.speed = max(
                0,
                min(80, (vehicle.speed or 35) + round(uniform(-3, 3))),  # nosec B311
            )
            vehicle.heading = int(((vehicle.heading or 0) + uniform(-8, 8)) % 360)  # nosec B311

        await db.commit()
