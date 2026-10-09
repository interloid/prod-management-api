from urllib.parse import quote

from fastapi import Request
from redis.asyncio import Redis

from app.core.settings import settings


def create_redis() -> Redis:
    if settings.REDIS_URL:
        return Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
        )

    return Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        username=settings.REDIS_USERNAME,
        password=settings.REDIS_PASSWORD,
        decode_responses=True,
    )


async def get_redis(request: Request) -> Redis:
    return request.app.state.redis


def get_redis_uri() -> str:
    if settings.REDIS_URL:
        return settings.REDIS_URL

    username = quote(settings.REDIS_USERNAME)

    if settings.REDIS_PASSWORD:
        password = quote(settings.REDIS_PASSWORD)
        auth = f"{username}:{password}@"
    else:
        auth = f"{username}@"

    return (
        f"redis://{auth}{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
    )
