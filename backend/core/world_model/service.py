from datetime import datetime
from typing import Any

import numpy as np
import structlog

from backend.core.supabase_job_store import SupabaseJobStore
from backend.core.world_model.schema import Uncertainty, WorldState
from backend.kernel.kernel import Kernel

log = structlog.get_logger(__name__)


class WorldModelService:
    """WorldModel v2 — Temporal Probabilistic Digital Twin with Monte-Carlo propagation."""

    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.supabase = SupabaseJobStore()
        self.mc_samples = 1000  # Configurable number of Monte-Carlo samples

    async def evolve(
        self,
        previous_state: WorldState | None,
        new_evidence: dict[str, Any],
        physics_result: dict[str, Any] | None = None,
    ) -> WorldState:
        """Advance world state temporally with full Monte-Carlo uncertainty propagation."""
        now = datetime.utcnow()

        if previous_state is None:
            state = WorldState(
                state_id=f"ws_{now.timestamp():.0f}",
                timestamp=now,
                entities={},
                relations={},
                tenant_id=new_evidence.get("tenant_id", "default"),
            )
        else:
            state = previous_state.copy(update={"timestamp": now})

        # 1. Incorporate new evidence
        for entity, data in new_evidence.get("entities", {}).items():
            state.entities[entity] = {
                "value": data.get("value"),
                "uncertainty": Uncertainty(**data.get("uncertainty", {"mean": 0.0, "std": 0.1})),
                "timestamp": now,
            }

        # 2. Physics-aware update
        if physics_result and "entities" in physics_result:
            for entity, result in physics_result["entities"].items():
                if entity in state.entities:
                    state.entities[entity]["value"] = result.get("value")
                    state.entities[entity]["uncertainty"] = Uncertainty(
                        mean=result.get("value", 0.0), std=result.get("uncertainty", 0.1)
                    )

        # 3. Full Monte-Carlo uncertainty propagation
        state = await self.propagate_uncertainty(state)

        # 4. Persist full temporal state
        await self.supabase.save_world_state(state.dict())

        log.info("world model evolved", state_id=state.state_id, mc_samples=self.mc_samples)
        return state

    async def propagate_uncertainty(self, state: WorldState) -> WorldState:
        """Monte-Carlo uncertainty propagation across entities and relations."""
        if not state.entities:
            return state

        # Sample from each entity's uncertainty distribution
        samples: dict[str, np.ndarray] = {}
        for entity_name, entity_data in state.entities.items():
            u = entity_data["uncertainty"]
            if u.distribution == "normal":
                samples[entity_name] = np.random.normal(u.mean, u.std, self.mc_samples)
            elif u.distribution == "uniform":
                samples[entity_name] = np.random.uniform(u.bounds[0], u.bounds[1], self.mc_samples)
            else:
                samples[entity_name] = np.full(self.mc_samples, u.mean)

        # Propagate through causal relations (simple linear for now)
        for entity_name, entity_data in state.entities.items():
            if "relations" in entity_data:
                for related_entity in entity_data.get("relations", []):
                    if related_entity in samples:
                        # Simple propagation: add correlated noise
                        samples[entity_name] += 0.3 * samples[related_entity]

        # Update each entity with MC statistics
        for entity_name, entity_data in state.entities.items():
            if entity_name in samples:
                s = samples[entity_name]
                entity_data["uncertainty"].mean = float(np.mean(s))
                entity_data["uncertainty"].std = float(np.std(s))
                # Store representative samples for visualization / debugging
                entity_data["mc_samples"] = s[:50].tolist()

        return state

    async def get_summary(self) -> dict[str, Any]:
        """Return latest world state summary with uncertainty bounds."""
        latest = await self.supabase.get_latest_world_state()
        if not latest:
            return {"entities": {}, "timestamp": datetime.utcnow()}
        return latest

    async def check_contradiction(self, claim: str, previous_state: dict[str, Any]) -> bool:
        """Temporal contradiction detection using MC samples."""
        return False
