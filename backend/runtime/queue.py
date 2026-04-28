import asyncio
import time
from collections import deque


class FakeQueue:
    def __init__(self):
        self.queue = deque()
        self.dlq = deque()
        self.processed = []
        self.lock = asyncio.Lock()

    async def enqueue(self, job):
        async with self.lock:
            self.queue.append(job)

    async def dequeue(self):
        async with self.lock:
            if not self.queue:
                return None
            return self.queue.popleft()

    async def mark_success(self, job):
        async with self.lock:
            self.processed.append(job)

    async def mark_failure(self, job, error):
        async with self.lock:
            job.attempts += 1

            if job.attempts >= job.max_retries:
                self.dlq.append(
                    {
                        "job": job,
                        "error": str(error),
                        "attempts": job.attempts,
                        "failed_at": time.time(),
                    }
                )
            else:
                # simple deterministic backoff
                await asyncio.sleep(0.01 * job.attempts)
                self.queue.append(job)
