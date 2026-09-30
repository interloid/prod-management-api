from uuid import UUID

from fastapi import Depends
from redis.asyncio import Redis
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.dependencies import get_current_user
from app.core.settings import settings
from app.db.redis import get_redis
from app.exceptions.custom import TooManyRequestsException
from app.models.user_model import User

# def get_user_rate_limit_key(request: Request) -> str:
#     user_id = getattr(
#         request.state,
#         "rate_limit_user_id",
#         None,
#     )

#     if user_id is None:
#         return get_remote_address(request)

#     return f"user:{user_id}"

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.REDIS_URL,
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

    count = await redis.incr(key)

    if count == 1:
        await redis.expire(key, window_seconds)

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
