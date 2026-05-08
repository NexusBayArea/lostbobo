from typing import Any

import structlog

from backend.core.kernel.command_bus import command_bus
from backend.core.supabase_job_store import SupabaseJobStore
from backend.kernel.kernel import Kernel
from backend.runtime.cognition.cognitive_router import CognitiveRouter
from backend.runtime.cognition.execution_attention_graph import ExecutionNode
from backend.runtime.cognition.multi_res_cognition import MultiResolutionCognition
from backend.runtime.cognition.novelty_scorer import NoveltyScorer

log = structlog.get_logger(__name__)


class SwarmCoordinator:
    """Extended with structured intermediate cognition + entropy/novelty monitoring."""

    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.supabase = SupabaseJobStore()
        self.cognition_graph = kernel.services["execution_graph"]
        self.multi_res = MultiResolutionCognition(kernel)
        self.cognitive_router = CognitiveRouter(kernel)
        self.novelty_scorer = NoveltyScorer(kernel)

    async def evaluate(self, payload: dict[str, Any]) -> dict[str, Any]:
        job_id = payload.get("job_id") or await self.supabase.create_job("swarm_evaluate", payload)

        # 1. Multi-Resolution Context Retrieval
        local_state = await self.multi_res.get_local_state(job_id)
        global_state = await self.multi_res.get_global_state()
        fused_context = await self.multi_res.fuse_states(local_state, global_state)

        # 2. Sparse Cognitive Routing
        routing_result = await self.cognitive_router.route(
            {**payload, "job_id": job_id, "fused_context": fused_context}
        )

        # 3. Parallel Agent Execution with Cognition Nodes
        agent_results = {}
        for agent_name, agent_payload in routing_result["results"].items():
            node = ExecutionNode(
                node_id=f"{job_id}-{agent_name}-{len(agent_results)}",
                parent_id=job_id,
                operation=f"swarm_agent_{agent_name}",
                state_hash=await self.kernel.services["state_hasher"].hash(agent_payload),
                trust_score=0.0,
                confidence=0.0,
                token_cost=0,
                timestamp="now",
            )
            await self.cognition_graph.add_node(node, job_id)

            # Execute via Kernel Command Bus
            result = await command_bus.route(
                {
                    "type": "AGENT_RUN",
                    "payload": {"agent": agent_name, "input": {**agent_payload, "cognition_context": fused_context}},
                }
            )

            agent_results[agent_name] = result

            node.trust_score = result.get("trust_score", 0.0)
            node.confidence = result.get("confidence", 0.0)
            await self.cognition_graph.add_node(node, job_id)

        # 4. Entropy / Novelty Scoring
        novelty_score = await self.novelty_scorer.compute(
            {"agent_results": agent_results, "fused_context": fused_context, "job_id": job_id}
        )

        # 5. Final Safety + Trust Check
        safety_result = await command_bus.route(
            {
                "type": "SAFETY_CHECK_EXECUTION",
                "payload": {
                    "job_id": job_id,
                    "state": {"agent_results": agent_results, "novelty": novelty_score},
                    "is_swarm_step": True,
                },
            }
        )

        if not safety_result.safe:
            return {"decision": "ABORT", "reason": safety_result.reason}

        final_report = {
            "job_id": job_id,
            "active_agents": routing_result["active_paths"],
            "results": agent_results,
            "fused_cognition": fused_context,
            "novelty_score": novelty_score,
            "decision": "PROCEED" if novelty_score > 0.4 else "ABORT_LOW_NOVELTY",
        }

        await self.supabase.update_job(job_id, status="completed", result=final_report)
        return final_report
