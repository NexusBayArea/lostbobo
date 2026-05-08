from dataclasses import dataclass
from datetime import datetime
from typing import Any

from backend.core.supabase_job_store import SupabaseJobStore
from backend.kernel.kernel import Kernel


@dataclass
class LocalCognitiveState:
    task_id: str
    current_step: str
    active_tools: list[str]
    local_memory: dict[str, Any]
    current_claims: list[dict[str, Any]]
    confidence: float
    timestamp: str


@dataclass
class GlobalCognitiveState:
    world_model_summary: dict[str, Any]
    trust_history: dict[str, Any]
    agent_reputation: dict[str, Any]
    historical_failures: list[dict[str, Any]]
    user_intent_vector: list[float]
    risk_telemetry: dict[str, Any]
    global_novelty_score: float


class MultiResolutionCognition:
    """Preserves both local high-fidelity reasoning and global context."""

    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.supabase = SupabaseJobStore()

    async def get_local_state(self, job_id: str) -> LocalCognitiveState:
        data = await self.supabase.get_latest_cognition_node(job_id) or {}
        return LocalCognitiveState(
            task_id=job_id,
            current_step=data.get("operation", "unknown"),
            active_tools=data.get("active_tools", []),
            local_memory=data.get("local_memory", {}),
            current_claims=data.get("claims", []),
            confidence=data.get("confidence", 0.0),
            timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
        )

    async def get_global_state(self) -> GlobalCognitiveState:
        return GlobalCognitiveState(
            world_model_summary=await self.kernel.services["world_model"].get_summary(),
            trust_history=await self.kernel.services["trust"].get_history_summary(),
            agent_reputation=await self.kernel.services["safety"].get_agent_reputation(),
            historical_failures=await self.supabase.get_historical_failures(limit=20),
            user_intent_vector=[],
            risk_telemetry=await self.kernel.services["safety"].get_risk_telemetry(),
            global_novelty_score=await self.kernel.services["cognition"].compute_novelty(),
        )

    async def fuse_states(self, local: LocalCognitiveState, global_state: GlobalCognitiveState) -> dict[str, Any]:
        fused = {
            "local": local.__dict__,
            "global": global_state.__dict__,
            "attention_guidance": await self.kernel.services["execution_graph"].attend(
                query=local.current_step, job_id=local.task_id, top_k=6
            ),
        }
        await self.supabase.record_event("cognition_fusion", fused)
        return fused
