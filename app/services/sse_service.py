import asyncio
from typing import Any


class SSEConnectionManager:
    def __init__(self) -> None:
        self.connections: set[asyncio.Queue[Any]] = set()

    async def subscribe(self) -> asyncio.Queue[Any]:
        queue: asyncio.Queue[Any] = asyncio.Queue()

        self.connections.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[Any]) -> None:
        self.connections.discard(queue)

    async def broadcast(self, event: Any) -> None:
        for queue in self.connections.copy():
            await queue.put(event)


sse_manager = SSEConnectionManager()
