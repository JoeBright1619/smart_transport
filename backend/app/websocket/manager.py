from __future__ import annotations

import asyncio
import json
import logging
from collections import defaultdict
from typing import Any

from fastapi import WebSocket
from redis.asyncio import Redis
from starlette.websockets import WebSocketState

from app.core.config import settings

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self, redis_url: str = settings.REDIS_URL) -> None:
        self.active_connections: dict[str, set[WebSocket]] = defaultdict(set)
        self.redis_url = redis_url
        self._redis: Redis | None = None
        self._listener_tasks: dict[str, asyncio.Task[None]] = {}
        self._lock = asyncio.Lock()

    @staticmethod
    def channel_for_tenant(tenant_id: str) -> str:
        return f"vehicle_updates:{tenant_id}"

    async def connect(self, websocket: WebSocket, tenant_id: str) -> None:
        await websocket.accept()
        async with self._lock:
            self.active_connections[tenant_id].add(websocket)
            await self._ensure_redis_listener(tenant_id)

    async def disconnect(self, websocket: WebSocket, tenant_id: str) -> None:
        async with self._lock:
            connections = self.active_connections.get(tenant_id)
            if connections is None:
                return

            connections.discard(websocket)
            if connections:
                return

            self.active_connections.pop(tenant_id, None)
            task = self._listener_tasks.pop(tenant_id, None)
            if task is not None:
                task.cancel()

    async def broadcast_to_tenant(
        self, tenant_id: str, message: dict[str, Any]
    ) -> None:
        connections = tuple(self.active_connections.get(tenant_id, set()))
        if not connections:
            return

        stale_connections: list[WebSocket] = []
        for websocket in connections:
            try:
                if websocket.client_state != WebSocketState.CONNECTED:
                    stale_connections.append(websocket)
                    continue

                await websocket.send_json(message)
            except Exception:
                logger.warning("Dropping failed websocket for tenant %s", tenant_id)
                stale_connections.append(websocket)

        if stale_connections:
            async with self._lock:
                current_connections = self.active_connections.get(tenant_id)
                if current_connections is None:
                    return

                for websocket in stale_connections:
                    current_connections.discard(websocket)

                if not current_connections:
                    self.active_connections.pop(tenant_id, None)
                    task = self._listener_tasks.pop(tenant_id, None)
                    if task is not None:
                        task.cancel()

    async def subscribe_to_tenant(self, tenant_id: str) -> None:
        await self._ensure_redis_listener(tenant_id)

    async def publish_to_tenant(self, tenant_id: str, message: dict[str, Any]) -> None:
        redis = await self._get_redis()
        await redis.publish(
            self.channel_for_tenant(tenant_id),
            json.dumps(message),
        )

    async def close(self) -> None:
        async with self._lock:
            tasks = list(self._listener_tasks.values())
            self._listener_tasks.clear()
            self.active_connections.clear()

        for task in tasks:
            task.cancel()

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        if self._redis is not None:
            await self._redis.close()
            self._redis = None

    async def _ensure_redis_listener(self, tenant_id: str) -> None:
        task = self._listener_tasks.get(tenant_id)
        if task is not None and not task.done():
            return

        self._listener_tasks[tenant_id] = asyncio.create_task(
            self._listen_to_tenant_channel(tenant_id)
        )

    async def _get_redis(self) -> Redis:
        if self._redis is None:
            self._redis = Redis.from_url(self.redis_url, decode_responses=True)
        return self._redis

    async def _listen_to_tenant_channel(self, tenant_id: str) -> None:
        channel = self.channel_for_tenant(tenant_id)
        pubsub = None
        try:
            redis = await self._get_redis()
            pubsub = redis.pubsub()
            await pubsub.subscribe(channel)

            async for redis_message in pubsub.listen():
                if redis_message.get("type") != "message":
                    continue

                payload = redis_message.get("data")
                message = self._decode_message(payload)
                await self.broadcast_to_tenant(tenant_id, message)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Redis listener failed for channel %s", channel)
        finally:
            if pubsub is not None:
                await pubsub.unsubscribe(channel)
                await pubsub.close()

    @staticmethod
    def _decode_message(payload: Any) -> dict[str, Any]:
        if isinstance(payload, dict):
            return payload

        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")

        if isinstance(payload, str):
            try:
                decoded = json.loads(payload)
            except json.JSONDecodeError:
                return {"type": "vehicle_update", "data": payload}

            if isinstance(decoded, dict):
                return decoded

            return {"type": "vehicle_update", "data": decoded}

        return {"type": "vehicle_update", "data": payload}


manager = ConnectionManager()
