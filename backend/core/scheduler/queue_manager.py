import asyncio
from typing import Any


class QueueManager:
    def __init__(self):
        self.queue = asyncio.Queue()

    async def enqueue(self, priority: str, workload: Any):
        # Simplistic priority handling
        await self.queue.put((priority, workload))

    async def dequeue(self) -> Any | None:
        if self.queue.empty():
            return None
        return await self.queue.get()
