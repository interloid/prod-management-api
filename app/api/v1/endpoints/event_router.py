import asyncio
from collections.abc import AsyncIterable

from fastapi import APIRouter, Depends
from fastapi.sse import EventSourceResponse, ServerSentEvent

from app.api.dependencies import get_current_user
from app.services.sse_service import sse_manager

router = APIRouter(
    prefix="/events",
    tags=["Events"],
    dependencies=[Depends(get_current_user)],
)


@router.get("", response_class=EventSourceResponse)
async def events() -> AsyncIterable[ServerSentEvent]:
    queue = await sse_manager.subscribe()

    try:
        while True:
            try:
                event = await asyncio.wait_for(
                    queue.get(),
                    timeout=15,
                )
                yield event

            except TimeoutError:
                yield ServerSentEvent(comment="ping")

    finally:
        sse_manager.unsubscribe(queue)
