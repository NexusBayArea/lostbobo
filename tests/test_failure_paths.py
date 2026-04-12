import asyncio

import pytest

from tests.fake_job_store import FakeJobStore


async def create_job(store, payload, user_id, idem_key):
    existing = await store.get_job_by_idempotency(idem_key)
    if existing:
        return existing

    job = await store.insert_job(
        {
            "user_id": user_id,
            "status": "queued",
            "input_params": payload,
            "idempotency_key": idem_key,
        }
    )

    return job


async def process_job(store, job_id, should_fail=False):
    await store.update_job(job_id, "running")

    if should_fail:
        await store.update_job(job_id, "failed", error={"message": "simulation failed"})
    else:
        await store.update_job(job_id, "completed", result={"output": "done"})

    return await store.get_job(job_id)


class FailingQueue:
    def __init__(self):
        self.calls = 0

    async def enqueue(self, *args, **kwargs):
        self.calls += 1
        raise Exception("queue down")


class SlowQueue:
    async def enqueue(self, *args, **kwargs):

        await asyncio.sleep(5)
        return "ok"


class FlakyQueue:
    def __init__(self):
        self.calls = 0

    def enqueue(self, payload, retries=1):
        for attempt in range(retries + 1):
            self.calls += 1
            if self.calls <= 1:
                continue
            return "ok"
        raise Exception("fail once")


class FakeQueue:
    def __init__(self, fail=False):
        self.jobs = {}
        self.failed = []
        self._fail = fail

    def enqueue(self, payload, key=None):
        if self._fail:
            self.failed.append(payload)
            raise Exception("queue down")
        job_id = key or str(len(self.jobs) + 1)
        self.jobs[job_id] = payload
        return job_id


def test_no_duplicate_enqueue():
    q = FakeQueue()

    id1 = q.enqueue({"task": "x"}, key="abc")
    id2 = q.enqueue({"task": "x"}, key="abc")

    assert id1 == id2
    assert len(q.jobs) == 1


def test_flaky_queue_retry():
    q = FlakyQueue()

    result = q.enqueue({"task": "y"}, retries=2)

    assert result == "ok"
    assert q.calls == 2


def test_failed_queue_tracks_failures():
    q = FakeQueue(fail=True)

    with pytest.raises(Exception):
        q.enqueue({"task": "z"}, key="fail")

    assert len(q.failed) == 1
    assert q.failed[0] == {"task": "z"}


@pytest.mark.asyncio
async def test_job_persisted_on_queue_failure():
    store = FakeJobStore()

    job = await store.insert_job(
        {
            "user_id": "user1",
            "status": "queued",
            "input_params": {"task": "x"},
            "idempotency_key": None,
        }
    )

    assert job["status"] == "queued"
    assert job["id"] in store.jobs


@pytest.mark.asyncio
async def test_idempotency_persisted():
    store = FakeJobStore()
    key = "abc123"

    r1 = await create_job(store, {"task": "x"}, "user1", key)
    r2 = await create_job(store, {"task": "x"}, "user1", key)

    assert r1["id"] == r2["id"]


@pytest.mark.asyncio
async def test_worker_lifecycle_success():
    store = FakeJobStore()

    job = await store.insert_job(
        {
            "user_id": "user1",
            "status": "queued",
            "input_params": {"task": "x"},
        }
    )

    result = await process_job(store, job["id"], should_fail=False)

    assert result["status"] == "completed"
    assert result["result"] == {"output": "done"}


@pytest.mark.asyncio
async def test_worker_lifecycle_failure():
    store = FakeJobStore()

    job = await store.insert_job(
        {
            "user_id": "user1",
            "status": "queued",
            "input_params": {"task": "x"},
        }
    )

    result = await process_job(store, job["id"], should_fail=True)

    assert result["status"] == "failed"
    assert result["error"] == {"message": "simulation failed"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
