import asyncio


class FakeWorker:
    def __init__(self, queue, handler):
        self.queue = queue
        self.handler = handler
        self.running = False

    async def run_once(self):
        job = await self.queue.dequeue()
        if not job:
            return False

        try:
            await self.handler(job)
            await self.queue.mark_success(job)
        except Exception as e:
            await self.queue.mark_failure(job, e)

        return True

    async def run(self):
        self.running = True
        while self.running:
            processed = await self.run_once()
            if not processed:
                await asyncio.sleep(0.01)

    def stop(self):
        self.running = False
