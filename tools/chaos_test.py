import asyncio
from backend.runtime.chaos_monkey import chaos_monkey


async def run_chaos_suite(iterations: int = 50):
    chaos_monkey.config.enabled = True
    chaos_monkey.config.probability = 0.25  # higher for testing

    print(f"🚀 Starting Chaos Monkey suite — {iterations} iterations")

    for i in range(iterations):
        # Simulate swarm task
        try:
            await chaos_monkey.inject_chaos(
                f"swarm_task_{i}",
                asyncio.sleep(0.1),  # placeholder for real task
            )
        except Exception:
            pass  # expected

    print(
        f"✅ Chaos suite complete. Experiments: {chaos_monkey.experiments_run} | Failures injected: {chaos_monkey.failures_injected}"
    )


if __name__ == "__main__":
    asyncio.run(run_chaos_suite())
