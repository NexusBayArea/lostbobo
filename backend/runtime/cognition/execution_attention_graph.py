from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import structlog

from backend.core.supabase_job_store import SupabaseJobStore
from backend.kernel.kernel import Kernel

log = structlog.get_logger(__name__)


@dataclass
class ExecutionNode:
    node_id: str
    parent_id: str | None
    operation: str
    state_hash: str
    trust_score: float
    confidence: float
    token_cost: int
    timestamp: datetime
    metadata: dict[str, Any] = field(default_factory=dict)
    attention_score: float = 0.0


class ExecutionAttentionGraph:
    """Preserves structured intermediate cognition as addressable graph nodes."""

    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.supabase = SupabaseJobStore()

    async def add_node(self, node: ExecutionNode, job_id: str):
        """Persist high-fidelity reasoning checkpoint to Supabase"""
        await self.supabase.record_event(
            "cognition_node",
            {
                "job_id": job_id,
                "node_id": node.node_id,
                "parent_id": node.parent_id,
                "operation": node.operation,
                "state_hash": node.state_hash,
                "trust_score": node.trust_score,
                "confidence": node.confidence,
                "attention_score": node.attention_score,
                "metadata": node.metadata,
            },
        )
        log.info("cognition node recorded", node_id=node.node_id, operation=node.operation)

    async def attend(self, query: str, job_id: str, top_k: int = 8) -> list[ExecutionNode]:
        """Selective retrieval of relevant prior cognition states"""
        # Placeholder for real retrieval logic using DepthRegistry
        return []
