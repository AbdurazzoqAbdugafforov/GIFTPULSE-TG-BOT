"""Resilient Cache Manager with Redis and in-memory fallback."""

import json
import time
from typing import Any, Optional
import redis.asyncio as aioredis
from app.core.config import settings
from app.core.logging import logger


class ResilientCache:
    """Manages caching with Redis when available, falling back smoothly to in-memory cache."""

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or settings.REDIS_URL
        self._redis: Optional[aioredis.Redis] = None
        self._memory_store: dict[str, tuple[str, float | None]] = {}  # key -> (json_str, expire_timestamp)
        self._redis_available: bool = True
        self._last_warn_time: float = 0

    async def get_client(self) -> Optional[aioredis.Redis]:
        if not self._redis_available:
            return None
        if self._redis is None:
            try:
                self._redis = aioredis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_timeout=1.5,
                    socket_connect_timeout=1.5,
                )
                await self._redis.ping()
            except Exception as e:
                now = time.time()
                if now - self._last_warn_time > 60:
                    logger.warning(f"Redis unavailable ({e}), using in-memory fallback cache.")
                    self._last_warn_time = now
                self._redis_available = False
                self._redis = None
                return None
        return self._redis

    async def set_json(self, key: str, data: Any, ttl: int = 3600) -> None:
        """Store json data with TTL in seconds."""
        payload = json.dumps(data)
        client = await self.get_client()
        if client:
            try:
                await client.set(key, payload, ex=ttl)
                return
            except Exception as e:
                self._redis_available = False
                logger.warning(f"Redis set failed ({e}), using in-memory store.")
        expire_at = time.time() + ttl if ttl else None
        self._memory_store[key] = (payload, expire_at)

    async def get_json(self, key: str) -> Optional[Any]:
        """Fetch json data if not expired."""
        client = await self.get_client()
        if client:
            try:
                raw = await client.get(key)
                if raw:
                    return json.loads(raw)
                return None
            except Exception as e:
                self._redis_available = False
                logger.warning(f"Redis get failed ({e}), using in-memory store.")
        
        # In-memory fallback
        item = self._memory_store.get(key)
        if not item:
            return None
        payload, expire_at = item
        if expire_at and time.time() > expire_at:
            del self._memory_store[key]
            return None
        return json.loads(payload)

    async def delete(self, key: str) -> None:
        client = await self.get_client()
        if client:
            try:
                await client.delete(key)
            except Exception:
                self._redis_available = False
        if key in self._memory_store:
            del self._memory_store[key]

    async def is_healthy(self) -> bool:
        client = await self.get_client()
        if client:
            try:
                return await client.ping()
            except Exception:
                return False
        return True  # In-memory cache is operational


# Singleton instance
cache_manager = ResilientCache()
