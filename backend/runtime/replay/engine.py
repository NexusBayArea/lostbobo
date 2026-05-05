"""Environment Replay Engine — replay real telemetry with modifications."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass
from typing import Any

import numpy as np

from backend.runtime.cache.simulation_cache import SimulationCache, simulation_hash
from backend.runtime.cache.zfp import compress_field
from backend.runtime.provenance.graph import ProvenanceGraph, ProvenanceNode
from backend.runtime.validation.simulation_validator import SimulationValidator

log = logging.getLogger(__name__)


@dataclass
class ReplayRequest:
    flight_id: str
    timestamp: float
    telemetry: dict[str, Any]
    environment: dict[str, Any]
    modifications: dict[str, Any]
    version: str = "v1"


@dataclass
class ReplayResult:
    replay_id: str
    flight_id: str
    original_hash: str
    modified_hash: str
    outputs: dict
    zfp_fields: bytes | None = None
    provenance_node_id: str
    stability_delta: float
    success: bool


class EnvironmentReplayEngine:
    """Replay real flights with parameter/environment modifications."""

    def __init__(self):
        self.cache = SimulationCache()
        self.validator = SimulationValidator()
        self.graph = ProvenanceGraph()

    async def replay(self, req: ReplayRequest) -> ReplayResult:
        """Run or fetch replay with modifications."""
        base_hash = simulation_hash(
            {
                "flight_id": req.flight_id,
                "timestamp": req.timestamp,
                "telemetry_hash": hashlib.sha256(json.dumps(req.telemetry, sort_keys=True).encode()).hexdigest()[:16],
            }
        )

        modified_params = {**req.telemetry, **req.environment, **req.modifications}
        mod_hash = simulation_hash(modified_params)

        cached = await self.cache.get(modified_params)
        if cached:
            log.info("Replay cache hit: %s", mod_hash[:12])
            return ReplayResult(
                replay_id=f"replay-{mod_hash[:8]}",
                flight_id=req.flight_id,
                original_hash=base_hash,
                modified_hash=mod_hash,
                outputs=cached.outputs,
                zfp_fields=cached.zfp_fields,
                provenance_node_id="cached",
                stability_delta=0.0,
                success=True,
            )

        sim_result = await self._run_modified_simulation(req)

        zfp_data = compress_field(sim_result.get("velocity_field") or np.zeros((50, 50)))

        await self.cache.store(modified_params, sim_result, zfp_data)

        node = ProvenanceNode(
            node_id=mod_hash,
            node_type="replay",
            data={"flight_id": req.flight_id, "modifications": req.modifications},
            parent_ids=[base_hash],
        )
        await self.graph.add_node(node)

        return ReplayResult(
            replay_id=f"replay-{mod_hash[:8]}",
            flight_id=req.flight_id,
            original_hash=base_hash,
            modified_hash=mod_hash,
            outputs=sim_result,
            zfp_fields=zfp_data,
            provenance_node_id=node.node_id,
            stability_delta=sim_result.get("stability_delta", 0.0),
            success=sim_result.get("converged", False),
        )

    async def _run_modified_simulation(self, req: ReplayRequest) -> dict:
        """Stub for RunPod / kernel execution."""
        await asyncio.sleep(0.3)
        return {
            "converged": True,
            "max_tilt": 18.5,
            "stability_delta": 0.12,
            "velocity_field": np.random.rand(100, 100).astype(np.float32).tolist(),
        }
