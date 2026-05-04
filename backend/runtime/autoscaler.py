#!/usr/bin/env python3
"""
SimHPC RunPod Autoscaler
========================
Intelligent GPU fleet scaling based on queue depth + job priority.
"""

import asyncio
import os

from backend.runtime.queue import QUEUE


class RunPodAutoscaler:
    def __init__(self):
        self.api_key = os.getenv("RUNPOD_API_KEY")
        self.min_pods = int(os.getenv("MIN_WARM_WORKERS", 1))
        self.max_pods = int(os.getenv("MAX_PODS", 8))
        self.base_url = "https://api.runpod.io/graphql"

    def get_queue_depth(self) -> int:
        """Return current queue length."""
        return len(QUEUE.snapshot()) if hasattr(QUEUE, "snapshot") else 0

    def scale_fleet(self, target: int):
        """Scale RunPod pods to target count (stub - replace with real GraphQL)."""
        print(f"📈 Scaling fleet to {target} pods...")

        # Real implementation would use GraphQL mutation here
        # For now: logging only
        if self.api_key:
            print(f"   → Would call RunPod API to scale to {target} pods")
        else:
            print("   ⚠️  RUNPOD_API_KEY not set — scaling simulation only")

    async def run(self):
        print("🔄 SimHPC RunPod Autoscaler Started")

        while True:
            try:
                depth = self.get_queue_depth()
                target = max(self.min_pods, min(self.max_pods, (depth // 2) + 1))

                self.scale_fleet(target)
                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                print(f"Autoscaler error: {e}")
                await asyncio.sleep(60)


def main():
    scaler = RunPodAutoscaler()
    asyncio.run(scaler.run())


if __name__ == "__main__":
    main()
