from uuid import UUID

from fastapi import Depends
from redis.asyncio import Redis
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.dependencies import get_current_user
from app.db.redis import get_redis, get_redis_uri
from app.exceptions.custom import TooManyRequestsException
from app.models.user_model import User

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=get_redis_uri(),
)


async def check_user_rate_limit(
    redis: Redis,
    *,
    user_id: UUID,
    action: str,
    limit: int,
    window_seconds: int = 60,
) -> None:

    key = f"rate-limit:user:{user_id}:{action}"

    added = await redis.set(key, 1, ex=window_seconds, nx=True)

    if added:
        count = 1
    else:
        count = await redis.incr(key)

    if count > limit:
        raise TooManyRequestsException(
            message="Too many requests. Please try again later."
        )


async def enforce_write_rate_limit(
    current_user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
) -> None:

    await check_user_rate_limit(
        redis=redis,
        user_id=current_user.id,
        action="write",
        limit=60,
    )


async def enforce_read_rate_limit(
    current_user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
) -> None:

    await check_user_rate_limit(
        redis=redis,
        user_id=current_user.id,
        action="read",
        limit=100,
    )
