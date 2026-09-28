import json
from typing import Any

from fastapi.encoders import jsonable_encoder
from redis.asyncio import Redis
from redis.exceptions import RedisError

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
