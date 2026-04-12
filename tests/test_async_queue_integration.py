import pytest
from tests.fakes.fake_queue import FakeQueue, Job
from tests.fakes.fake_worker import FakeWorker


@pytest.mark.asyncio
async def test_job_success():
    queue = FakeQueue()

    async def handler(job):
        return "ok"

    worker = FakeWorker(queue, handler)

    await queue.enqueue(Job(id="1", payload={}))

    await worker.run_once()

    assert len(queue.processed) == 1
    assert len(queue.dlq) == 0


@pytest.mark.asyncio
async def test_retry_behavior():
    queue = FakeQueue()

    attempts = {"count": 0}

    async def handler(job):
        attempts["count"] += 1
        if attempts["count"] < 2:
            raise ValueError("fail once")

    worker = FakeWorker(queue, handler)

    await queue.enqueue(Job(id="1", payload={}, max_retries=3))

    # first attempt fails → requeued
    await worker.run_once()
    # second attempt succeeds
    await worker.run_once()

    assert len(queue.processed) == 1
    assert attempts["count"] == 2


@pytest.mark.asyncio
async def test_dead_letter_queue():
    queue = FakeQueue()

    async def handler(job):
        raise RuntimeError("always fails")

    worker = FakeWorker(queue, handler)

    await queue.enqueue(Job(id="1", payload={}, max_retries=2))

    # attempt 1
    await worker.run_once()
    # attempt 2
    await worker.run_once()
    # attempt 3 (goes to DLQ)
    await worker.run_once()

    assert len(queue.dlq) == 1
    assert len(queue.processed) == 0


@pytest.mark.asyncio
async def test_idempotency():
    queue = FakeQueue()

    seen = set()

    async def handler(job):
        if job.id in seen:
            raise RuntimeError("duplicate execution")
        seen.add(job.id)

    worker = FakeWorker(queue, handler)

    job = Job(id="1", payload={}, max_retries=3)

    await queue.enqueue(job)
    await queue.enqueue(job)  # duplicate

    await worker.run_once()
    await worker.run_once()

    assert len(seen) == 1
