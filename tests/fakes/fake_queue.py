import asyncio
from collections import deque
from dataclasses import dataclass
from typing import Any, Callable, Optional


@dataclass
class Job:
    id: str
    payload: dict
    attempts: int = 0
    max_retries: int = 3


class FakeQueue:
    """
    Deterministic in-memory queue for async worker testing.
    """

    def __init__(self):
        self.queue = deque()
        self.dlq = deque()
        self.processed = []
        self.lock = asyncio.Lock()

    async def enqueue(self, job: Job):
        async with self.lock:
            self.queue.append(job)

    async def dequeue(self) -> Optional[Job]:
        async with self.lock:
            if not self.queue:
                return None
            return self.queue.popleft()

    async def mark_success(self, job: Job):
        async with self.lock:
            self.processed.append(job)

    async def mark_failure(self, job: Job, error: Exception):
        async with self.lock:
            job.attempts += 1
            if job.attempts >= job.max_retries:
                self.dlq.append((job, str(error)))
            else:
                self.queue.append(job)  # retry
