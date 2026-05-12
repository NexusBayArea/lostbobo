from __future__ import annotations

import asyncio
import time
from typing import Dict, Optional

from backend.core.execution.models import ExecutionPriority, ExecutionRequest, ExecutionStatus


class LeaseTracker:
    def __init__(self):
        self._leases: Dict[str, float] = {}

    def acquire(self, execution_id: str, lease_seconds: int = 30) -> bool:
        now = time.time()
        if execution_id in self._leases and self._leases[execution_id] > now:
            return False
        self._leases[execution_id] = now + lease_seconds
        return True

    def release(self, execution_id: str):
        self._leases.pop(execution_id, None)

    def renew(self, execution_id: str, lease_seconds: int = 30):
        self._leases[execution_id] = time.time() + lease_seconds

    def is_leased(self, execution_id: str) -> bool:
        now = time.time()
        return execution_id in self._leases and self._leases[execution_id] > now


class KernelExecutionQueue:
    _PRIORITY_MAP = {
        ExecutionPriority.INTERACTIVE: 1,
        ExecutionPriority.SIMULATION: 2,
        ExecutionPriority.BACKGROUND: 3,
        ExecutionPriority.REPLAY: 4,
        ExecutionPriority.PLUGIN: 5,
    }

    _DECREASING_PRIORITY = [
        ExecutionPriority.INTERACTIVE,
        ExecutionPriority.SIMULATION,
        ExecutionPriority.BACKGROUND,
        ExecutionPriority.REPLAY,
        ExecutionPriority.PLUGIN,
    ]

    def __init__(self):
        self._queues: Dict[str, asyncio.PriorityQueue] = {p.value: asyncio.PriorityQueue() for p in ExecutionPriority}
        self.leases = LeaseTracker()
        self._retry_counts: Dict[str, int] = {}
        self._max_retries = 3

    async def enqueue(self, request: ExecutionRequest):
        prio = self._PRIORITY_MAP.get(request.priority, 3)
        queue = self._queues[request.priority.value]
        await queue.put((prio, request))

    async def dequeue(self) -> Optional[ExecutionRequest]:
        for priority in self._DECREASING_PRIORITY:
            queue = self._queues[priority.value]
            if not queue.empty():
                prio, request = await queue.get()
                if self.leases.acquire(request.execution_id):
                    return request
                await queue.put((prio, request))
        return None

    def mark_completed(self, execution_id: str):
        self.leases.release(execution_id)
        self._retry_counts.pop(execution_id, None)

    def mark_failed(self, execution_id: str) -> bool:
        count = self._retry_counts.get(execution_id, 0) + 1
        self._retry_counts[execution_id] = count
        self.leases.release(execution_id)
        return count <= self._max_retries

    async def requeue(self, request: ExecutionRequest):
        await self.enqueue(request)
