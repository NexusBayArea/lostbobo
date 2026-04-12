import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class FailingQueue:
    def __init__(self):
        self.calls = 0

    async def enqueue(self, *args, **kwargs):
        self.calls += 1
        raise Exception("queue down")


class SlowQueue:
    async def enqueue(self, *args, **kwargs):
        import asyncio

        await asyncio.sleep(5)
        return "ok"


class FlakyQueue:
    def __init__(self):
        self.calls = 0

    def enqueue(self, payload):
        self.calls += 1
        if self.calls < 2:
            raise Exception("fail once")
        return "ok"


class FakeQueue:
    def __init__(self):
        self.jobs = {}
        self.failed = []

    def enqueue(self, payload, key=None):
        try:
            job_id = key or str(len(self.jobs) + 1)
            self.jobs[job_id] = payload
            return job_id
        except Exception as e:
            self.failed.append(payload)
            raise


def test_no_duplicate_enqueue():
    q = FakeQueue()

    id1 = q.enqueue({"task": "x"}, key="abc")
    id2 = q.enqueue({"task": "x"}, key="abc")

    assert id1 == id2
    assert len(q.jobs) == 1


def test_flaky_queue_retry():
    q = FlakyQueue()

    result = q.enqueue({"task": "y"})

    assert result == "ok"
    assert q.calls == 2


def test_failed_queue_tracks_failures():
    q = FakeQueue()

    with pytest.raises(Exception):
        q.enqueue({"task": "z"}, key="fail")

    assert len(q.failed) == 1
    assert q.failed[0] == {"task": "z"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
