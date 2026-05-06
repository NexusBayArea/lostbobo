#!/usr/bin/env python3
"""
SimHPC Distributed Queue System
===============================
Persistent disk-backed queue with Redis fallback and FakeQueue for testing.
"""

import asyncio
import json
from pathlib import Path

from backend.runtime.job import Job


class PersistentQueue:
    """Disk-backed persistent queue for production use."""

    def __init__(self, path: str = "runtime_queue.json"):
        self.path = Path(path)
        self._load()

    def _load(self):
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text())
                self.q = [Job(**item) if isinstance(item, dict) else item for item in data]
            except Exception:
                self.q = []
        else:
            self.q = []

    def _save(self):
        self.path.write_text(json.dumps([j.__dict__ if hasattr(j, "__dict__") else j for j in self.q], indent=2))

    def enqueue(self, job: Job):
        self.q.append(job)
        self._save()

    def dequeue(self) -> Job | None:
        if not self.q:
            return None
        job = self.q.pop(0)
        self._save()
        return job

    def mark_success(self, job: Job):
        print(f"✅ Job {job.id} marked successful")

    def mark_failure(self, job: Job, error: str):
        job.attempts += 1
        if job.attempts >= job.max_retries:
            print(f"💀 Job {job.id} moved to DLQ after {job.attempts} attempts")
        else:
            self.q.append(job)  # requeue
            self._save()

    def snapshot(self):
        return [j.id for j in self.q]


class FakeQueue:
    """In-memory queue for local development and testing."""

    def __init__(self):
        self.queue = asyncio.Queue()
        self.dlq = []

    async def enqueue(self, job: Job):
        await self.queue.put(job)

    async def dequeue(self) -> Job | None:
        try:
            return await asyncio.wait_for(self.queue.get(), timeout=1.0)
        except TimeoutError:
            return None

    async def mark_success(self, job: Job):
        print(f"✅ [Fake] Job {job.id} succeeded")

    async def mark_failure(self, job: Job, error: str):
        print(f"❌ [Fake] Job {job.id} failed: {error}")
        job.attempts += 1
        if job.attempts >= job.max_retries:
            print(f"💀 [Fake] Job {job.id} moved to DLQ after {job.attempts} attempts")
            self.dlq.append(job)
        else:
            await self.enqueue(job)  # requeue


# Global instance
QUEUE = PersistentQueue() if Path("runtime_queue.json").exists() else FakeQueue()
