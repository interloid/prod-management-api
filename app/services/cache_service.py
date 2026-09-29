import json
from typing import Any
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.constants import CacheKeyConstants
from app.core.logging import get_logger

logger = get_logger(__name__)


class CacheService:
    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    async def get_json(self, key: str) -> Any | None:
        try:
            cached_value = await self.redis.get(key)

        except RedisError:
            logger.warning("Redis cache read failed", extra={"cached_key": key})
            return None
        if cached_value is None:
            return None

        try:
            return json.loads(cached_value)

        except (json.JSONDecodeError, TypeError):
            logger.warning(
                "Invalid JSON found in Redis cache", extra={"cached_key": key}
            )
            return None

    async def set_json(self, key: str, value: Any, ttl: int) -> None:

        encoded_value = jsonable_encoder(value)
        json_value = json.dumps(encoded_value)

        try:
            await self.redis.set(key, json_value, ex=ttl)

        except RedisError:
            logger.warning("Redis cache write failed", extra={"cached_key": key})
            return None

    async def delete_keys(self, *keys: str) -> None:

        if not keys:
            return

        try:
            await self.redis.delete(*keys)

        except RedisError:
            logger.warning(
                "Redis cache delete failed", extra={"cached_key": list(keys)}
            )
            return None

    async def delete_by_pattern(self, pattern: str) -> None:
        try:
            keys = []

            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                await self.delete_keys(*keys)

        except RedisError:
            logger.warning(
                "Redis cache pattern delete failed",
                extra={"pattern": pattern},
            )

    async def invalidate_product_list_cache(self) -> None:
        keys = await self.redis.smembers(CacheKeyConstants.PRODUCT_LIST_CACHE_KEYS)

        if not keys:
            return

        keys = [key.decode() if isinstance(key, bytes) else key for key in keys]

        await self.delete_keys(*keys)
        await self.delete_keys(CacheKeyConstants.PRODUCT_LIST_CACHE_KEYS)

    async def invalidate_product_cache(self, id: UUID) -> None:
        key = f"{CacheKeyConstants.PRODUCT_CACHE_PREFIX}{id}"

        await self.delete_keys(key)

    async def add_to_set(self, key: str, value: str) -> None:
        await self.redis.sadd(key, value)
