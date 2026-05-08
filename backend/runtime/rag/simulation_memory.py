import hashlib
from dataclasses import dataclass, field
from typing import Any

import structlog

from backend.core.supabase_job_store import SupabaseJobStore
from backend.kernel.kernel import Kernel

log = structlog.get_logger(__name__)


@dataclass
class SimulationMemoryEntry:
    sim_id: str
    domain: str
    state_hash: str
    output_hash: str
    trust_score: float
    verification_signature: str
    tags: list[str]
    timestamp: str
    metadata: dict[str, Any] = field(default_factory=dict)


class SimulationMemoryRetriever:
    """First-class retrieval of past simulation results as structured cognition."""

    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.supabase = SupabaseJobStore()

    async def store(self, payload: dict[str, Any]) -> str:
        """Store simulation output as memory entry"""
        sim_id = payload.get("sim_id") or f"sim_{hashlib.sha256(str(payload).encode()).hexdigest()[:12]}"

        entry = SimulationMemoryEntry(
            sim_id=sim_id,
            domain=payload.get("domain", "general"),
            state_hash=await self.kernel.services["state_hasher"].hash(payload.get("state", {})),
            output_hash=hashlib.sha256(str(payload.get("output", "")).encode()).hexdigest(),
            trust_score=payload.get("trust_score", 0.0),
            verification_signature=payload.get("verification_signature", ""),
            tags=payload.get("tags", []),
            timestamp="now",
            metadata=payload.get("metadata", {}),
        )

        await self.supabase.record_event("simulation_memory_stored", entry.__dict__)
        await self.kernel.services["execution_graph"].add_node(
            {"operation": "simulation_memory_store", "state_hash": entry.state_hash, "metadata": {"sim_id": sim_id}},
            sim_id,
        )

        return sim_id

    async def retrieve(self, query: str, domain: str | None = None, top_k: int = 10) -> list[SimulationMemoryEntry]:
        """Retrieve relevant past simulation memories."""
        return await self.supabase.search_simulation_memory(query, domain, top_k)
