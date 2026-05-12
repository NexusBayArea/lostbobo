from __future__ import annotations

import asyncio
import time
from typing import Any

from backend.core.determinism.seeds.deterministic_seed_manager import DeterministicSeedManager
from backend.core.hardware.isolation import GPUIsolationManager
from backend.runtime.gpu_worker.jit_loader import RuntimeLoader
from backend.runtime.gpu_worker.telemetry import TelemetryAgent
from backend.runtime.scientific.simulation_executor import ScientificSimulationExecutor

gpu_manager = GPUIsolationManager()
seed_manager = DeterministicSeedManager()
sci_executor = ScientificSimulationExecutor()
jit_loader = RuntimeLoader()

SIMULATION_CAPABILITIES = frozenset(
    {
        "physics.solve",
        "simulation.run",
        "fem.thermal",
        "ode.solve",
    }
)


async def execute_job(job: dict[str, Any], agent: TelemetryAgent) -> dict[str, Any]:
    execution_id = job["execution_id"]
    capability = job["capability"]

    seed = seed_manager.derive_seed(execution_id)
    seed_manager.apply_seed(seed)

    required_libs = job.get("required_libraries", [])
    try:
        jit_loader.load(required_libs)
    except ImportError as e:
        await agent.emit(execution_id, "job.failed", {"error": str(e)})
        raise

    await agent.emit(execution_id, "job.started", {"capability": capability})

    start = time.time()
    try:
        if capability in SIMULATION_CAPABILITIES:
            result = await sci_executor.execute(job)
            await agent.emit(execution_id, "job.completed", {"solver": job.get("solver_type")})
            return result

        await asyncio.sleep(2)
        result = {
            "output": f"simulated {capability}",
            "execution_id": execution_id,
            "deterministic_hash": "abc123",
        }

        duration = time.time() - start
        await agent.emit(execution_id, "job.completed", {"duration_ms": duration * 1000})

        return result
    except Exception as e:
        await agent.emit(execution_id, "job.failed", {"error": str(e)})
        raise
