import pytest
import asyncio
from runtime.job import Job
from runtime.queue import FakeQueue
from runtime.worker import FakeWorker


@pytest.mark.asyncio
async def test_idempotency():
    queue = FakeQueue()
    seen = set()

    async def handler(job):
        if job.id in seen:
            raise RuntimeError("duplicate execution")
        seen.add(job.id)

    worker = FakeWorker(queue, handler)

    job1 = Job(id="1", payload={})
    job2 = Job(id="1", payload={})  # separate instance

    await queue.enqueue(job1)
    await queue.enqueue(job2)

    await worker.run_once()
    await worker.run_once()

    assert len(seen) == 1


@pytest.mark.asyncio
async def test_timeout_handling():
    queue = FakeQueue()

    async def handler(job):
        await asyncio.sleep(2)  # exceeds timeout

    worker = FakeWorker(queue, handler, timeout=0.1)

    await queue.enqueue(Job(id="1", payload={}, max_retries=2))

    await worker.run_once()
    await worker.run_once()

    assert len(queue.dlq) == 1
