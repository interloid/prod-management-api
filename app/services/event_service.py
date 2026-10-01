import json

from fastapi.sse import ServerSentEvent
from redis.asyncio import Redis

from app.core.constants import EventChannelConstants
from app.core.logging import get_logger
from app.schemas.event import EventEnvelope
from app.services.sse_service import sse_manager

logger = get_logger(__name__)


class EventService:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def publish(self, event: EventEnvelope) -> None:

        logger.info(
            "EventService.publish() CALLED | event=%s | request_id=%s",
            event.event,
            event.request_id,
        )
        message = json.dumps(event.model_dump(mode="json"))

        result = await self.redis.publish(
            EventChannelConstants.SSE_EVENTS_CHANNEL,
            message,
        )

        logger.info(
            "SSE event published | receivers=%s",
            result,
        )

    async def subscribe(self) -> None:
        pubsub = self.redis.pubsub()

        channel = await pubsub.subscribe(
            EventChannelConstants.SSE_EVENTS_CHANNEL,
        )

        logger.info("SSE subscribed | channel=%s", channel)

        try:
            async for message in pubsub.listen():
                logger.info("Redis Pub/Sub message received | %s", message)

                if message["type"] != "message":
                    continue

                envelope = EventEnvelope.model_validate(
                    json.loads(message["data"]),
                )

                sse_event = ServerSentEvent(
                    event=envelope.event,
                    data=envelope.data,
                    id=envelope.request_id,
                )

                await sse_manager.broadcast(sse_event)

        finally:
            await pubsub.unsubscribe(
                EventChannelConstants.SSE_EVENTS_CHANNEL,
            )
            await pubsub.aclose()
