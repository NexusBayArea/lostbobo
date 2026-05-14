from __future__ import annotations

import asyncio
import heapq
from dataclasses import dataclass
from enum import IntEnum
from typing import Any


class Priority(IntEnum):
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BEST_EFFORT = 4


@dataclass
class SchedulingRequest:
    priority: Priority
    enqueue_time: float
    capability: str = ""
    invocation_id: str = ""
    payload: Any = None
    tenant_id: str = "default"

    def __lt__(self, other: SchedulingRequest) -> bool:
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.enqueue_time < other.enqueue_time


class PriorityQueue:
    def __init__(self):
        self._heap: list[SchedulingRequest] = []
        self._lock = asyncio.Lock()
        self._total_enqueued = 0
        self._total_dequeued = 0

    async def enqueue(self, request: SchedulingRequest) -> None:
        async with self._lock:
            heapq.heappush(self._heap, request)
            self._total_enqueued += 1

    async def dequeue(self) -> SchedulingRequest | None:
        async with self._lock:
            if self._heap:
                self._total_dequeued += 1
                return heapq.heappop(self._heap)
            return None

    @property
    async def queue_depth(self) -> int:
        async with self._lock:
            return len(self._heap)

    @property
    async def stats(self) -> dict[str, Any]:
        async with self._lock:
            return {
                "depth": len(self._heap),
                "total_enqueued": self._total_enqueued,
                "total_dequeued": self._total_dequeued,
            }
