#!/usr/bin/env python3
"""
SimHPC Physics Worker
=====================
Background worker that consumes jobs and executes MFEM/SUNDIALS nodes.
"""

import asyncio
import sys
from pathlib import Path

# Path setup
if str(Path(__file__).resolve().parents[2]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.runtime.dag_executor import execute_node
from backend.runtime.job import Job
from backend.runtime.queue import FakeQueue, PersistentQueue


async def process_job(job: Job):
    """Execute a single simulation job."""
    print(f"🔧 Processing job {job.id}")
    try:
        result = execute_node(job.payload)
        status = "success" if result == 0 else "failed"
        print(f"✅ Job {job.id} completed: {status}")
        return result
    except Exception as e:
        print(f"❌ Job {job.id} failed: {e}")
        raise


async def main():
    print("🚀 SimHPC Physics Worker Started")

    # Use persistent queue in production, FakeQueue for local testing
    queue = PersistentQueue() if Path("runtime_queue.json").exists() else FakeQueue()

    while True:
        try:
            job = await queue.dequeue() if hasattr(queue, "dequeue") else None
            if not job:
                await asyncio.sleep(1)
                continue

            await process_job(job)
            await queue.mark_success(job) if hasattr(queue, "mark_success") else None

        except Exception as e:
            print(f"Worker error: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("👋 Worker shutdown")
