from collections.abc import AsyncIterable
from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from fastapi.sse import EventSourceResponse, ServerSentEvent

from app.api.dependencies import get_redis
from app.schemas.event import EventEnvelope
from app.services.event_service import EventService
from app.services.sse_service import sse_manager

router = APIRouter(
    prefix="/events",
    tags=["Events"],
    # dependencies=[Depends(get_current_user)],
)


@router.get("", response_class=EventSourceResponse)
async def events() -> AsyncIterable[ServerSentEvent]:
    queue = await sse_manager.subscribe()

    try:
        while True:
            event = await queue.get()
            yield event

    finally:
        sse_manager.unsubscribe(queue)


@router.post("/test")
async def test_event() -> dict[str, str]:
    await sse_manager.broadcast(
        ServerSentEvent(
            event="test",
            data={"message": "Hello from FastAPI"},
            id="test-1",
        )
    )

    return {"status": "sent"}


@router.post("/test-redis")
async def test_redis_event(
    redis=Depends(get_redis),
) -> dict[str, str]:
    event = EventEnvelope(
        event="test.redis",
        request_id="test-redis-1",
        timestamp=datetime.now(UTC),
        data={
            "message": "Hello through Redis Pub/Sub",
        },
    )

    await EventService(redis).publish(event)

    return {"status": "published"}
