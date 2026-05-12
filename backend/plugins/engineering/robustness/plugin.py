"""
Robustness Analysis Plugin for SimHPC

Capabilities:
    engineering.robustness.run     → accepts payload, returns batch future
    engineering.robustness.status  → returns progress of a batch
"""

from __future__ import annotations

import time
import uuid
from typing import Any

import numpy as np

from backend.core.execution.models import ExecutionPriority, ExecutionRequest
from backend.core.memory.fabric.execution_memory import ExecutionMemoryRecord
from backend.core.sdk.base_plugin import BasePlugin
from backend.plugins.engineering.robustness.manifest import manifest


class Plugin(BasePlugin):
    manifest = manifest

    async def register(self, kernel) -> None:
        self.kernel = kernel
        kernel.capabilities.register("engineering.robustness.run", self.run_analysis)
        kernel.capabilities.register("engineering.robustness.status", self.get_status)

    async def run_analysis(self, payload: dict) -> dict[str, Any]:
        tenant_id = payload["tenant_id"]
        parameters = payload["parameters"]
        method_str = payload.get("sampling_method", "%10%")
        num_runs = payload["num_runs"]
        solver_type = payload.get("solver_type", "mfem")

        seed = payload.get("seed", int(time.time()))
        sampler = _ParameterSampler(seed)
        perturbations = sampler.generate(parameters, method_str, num_runs)

        batch_id = str(uuid.uuid4())
        execution_ids = []
        for param_set in perturbations:
            exec_req = ExecutionRequest(
                tenant_id=tenant_id,
                plugin_name="robustness",
                capability="simulation.run",
                inputs={
                    "solver_type": solver_type,
                    "parameters": param_set,
                    "mesh_data": payload.get("mesh_data"),
                },
                priority=ExecutionPriority.SIMULATION,
                timeout_seconds=600,
                checkpoint_enabled=False,
            )
            await self.kernel.capabilities.invoke("execution.submit", exec_req.model_dump())
            execution_ids.append(exec_req.execution_id)

        batch_rec = ExecutionMemoryRecord(
            memory_id=batch_id,
            tenant_id=tenant_id,
            plugin_name="robustness",
            timestamp=time.time(),
            dag_id=batch_id,
            node_id="batch",
            execution_state={
                "execution_ids": execution_ids,
                "total": len(execution_ids),
                "completed": 0,
                "results": [],
                "sampling_method": method_str,
                "parameters": parameters,
                "solver_type": solver_type,
            },
        )
        await self.kernel.memory_fabric.insert(batch_rec)

        return {
            "batch_id": batch_id,
            "execution_count": len(execution_ids),
            "status": "queued",
        }

    async def get_status(self, payload: dict) -> dict[str, Any]:
        batch_id = payload["batch_id"]
        rec = self.kernel.memory_fabric.records.get(batch_id)
        if rec is None:
            return {"status": "unknown"}
        state = rec.execution_state
        return {
            "batch_id": batch_id,
            "completed": state["completed"],
            "total": state["total"],
            "status": "completed" if state["completed"] == state["total"] else "running",
        }


class _ParameterSampler:
    def __init__(self, seed: int):
        self.rng = np.random.RandomState(seed)

    def generate(self, param_configs: list[dict], method: str, n_runs: int) -> list[dict]:
        perturbable = [p for p in param_configs if p.get("perturbable", True)]
        base_dict = {p["name"]: p["base"] for p in param_configs}
        if method in ("%5%", "%10%"):
            pct = 0.05 if method == "%5%" else 0.10
            return self._percentage(base_dict, perturbable, pct, n_runs)
        elif method == "latin_hypercube":
            return self._lhs(base_dict, perturbable, n_runs)
        elif method == "sobol":
            return self._lhs(base_dict, perturbable, n_runs)
        raise ValueError(f"Unknown sampling method: {method}")

    def _percentage(self, base, params, pct, n):
        results = []
        for _ in range(n):
            run = base.copy()
            for p in params:
                factor = 1.0 + self.rng.uniform(-pct, pct)
                val = p["base"] * factor
                if "min" in p:
                    val = max(val, p["min"])
                if "max" in p:
                    val = min(val, p["max"])
                run[p["name"]] = val
            results.append(run)
        return results

    def _lhs(self, base, params, n):
        dim = len(params)
        samples = np.zeros((n, dim))
        for j in range(dim):
            perm = self.rng.permutation(n)
            samples[:, j] = (perm + self.rng.uniform(0, 1, n)) / n
        results = []
        for i in range(n):
            run = base.copy()
            for j, p in enumerate(params):
                factor = 0.9 + samples[i, j] * 0.2
                val = p["base"] * factor
                if "min" in p:
                    val = max(val, p["min"])
                if "max" in p:
                    val = min(val, p["max"])
                run[p["name"]] = val
            results.append(run)
        return results
