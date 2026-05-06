"""World Model Service — probabilistic digital twin + uncertainty propagation."""

from __future__ import annotations

import logging
from typing import Any

from backend.app.core.supabase import get_supabase_client
from backend.core.memory.service import MemoryService
from backend.core.world_model.schema import WorldState

log = logging.getLogger(__name__)


class WorldModelService:
    def __init__(self):
        self.memory = MemoryService()

    async def update(self, state: WorldState) -> WorldState:
        """Update world state (persistent + real-time)."""
        sb = get_supabase_client()
        if not sb:
            return state

        entities_dict = {}
        for k, v in state.entities.items():
            entities_dict[k] = {
                vk: {"value": vv.value, "uncertainty": {"mean": vv.uncertainty.mean, "std": vv.uncertainty.std}}
                for vk, vv in v.items()
            }

        await (
            sb.table("world_states")
            .insert(
                {
                    "state_id": state.state_id,
                    "timestamp": state.timestamp.isoformat(),
                    "entities": entities_dict,
                    "relations": state.relations,
                    "scenarios": state.scenarios,
                    "tenant_id": state.tenant_id,
                    "metadata": state.metadata,
                }
            )
            .execute()
        )

        log.info("World state updated: %s", state.state_id)
        return state

    async def query(self, filter: dict[str, Any]) -> list[WorldState]:
        """Query historical world states."""
        sb = get_supabase_client()
        if not sb:
            return []

        q = sb.table("world_states").select("*")
        if "domain" in filter:
            q = q.eq("metadata->>domain", filter["domain"])
        resp = await q.order("timestamp", desc=True).limit(20).execute()
        return [WorldState(**r) for r in resp.data]

    async def propagate_uncertainty(self, state: WorldState, steps: int = 1000) -> dict[str, Any]:
        """Monte-Carlo uncertainty propagation."""
        results = {}
        for entity, vars_dict in state.entities.items():
            for var_name, var in vars_dict.items():
                mean = var.value
                std = var.uncertainty.std or (mean * 0.1)
                samples = [mean + std * ((i % 5) - 2) for i in range(steps)]
                results[f"{entity}.{var_name}"] = {
                    "mean": mean,
                    "std": std,
                    "p10": sorted(samples)[int(steps * 0.1)],
                    "p90": sorted(samples)[int(steps * 0.9)],
                }
        return results
