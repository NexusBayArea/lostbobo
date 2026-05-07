"""Speculative RAG + Agent Swarm Orchestrator with early exit and streaming."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from typing import Any

from backend.runtime.agent.graph_agent import GraphRAGAgent
from backend.runtime.agent.sim_retrieval_agent import SimulationRetrievalAgent
from backend.runtime.agent.vector_agent import VectorRAGAgent
from backend.runtime.fallback import FallbackResult, GenAIFallback
from backend.runtime.rag.router import RAGRouter
from backend.runtime.resilience import SwarmResilience

log = logging.getLogger(__name__)

# Score threshold that triggers early exit (skip waiting for slower agents)
_EARLY_EXIT_THRESHOLD = 0.85
# Early exit is only valid before this fraction of the total timeout has elapsed
_EARLY_EXIT_WINDOW = 0.70


@dataclass
class AgentResult:
    agent_name: str
    content: str
    score: float
    latency_ms: float
    evidence: list[dict] = field(default_factory=list)
    degraded: bool = False


class SpeculativeOrchestrator:
    """
    Runs multiple reasoning paths in parallel (vector, graph, simulation).
    """

    def __init__(self) -> None:
        self.rag_router = RAGRouter()
        self.vector_agent = VectorRAGAgent()
        self.graph_agent = GraphRAGAgent()
        self.sim_agent = SimulationRetrievalAgent()
        self.task_metrics: dict[str, dict] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def stream_query(
        self,
        query: str,
        tenant_id: str = "public",
        timeout_ms: int = 8000,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Speculative execution with streaming.
        """
        start = time.time()
        timeout_s = timeout_ms / 1000.0

        yield {"type": "start", "query": query}
        log.info("[Swarm] Starting speculative query: %s", query)

        tasks: list[asyncio.Task] = [
            asyncio.create_task(
                self._run_agent_resilient(self.vector_agent, query, tenant_id, "vector"),
                name="agent_vector",
            ),
            asyncio.create_task(
                self._run_agent_resilient(self.graph_agent, query, tenant_id, "graph"),
                name="agent_graph",
            ),
            asyncio.create_task(
                self._run_agent_resilient(self.sim_agent, query, tenant_id, "simulation"),
                name="agent_simulation",
            ),
        ]

        best: AgentResult | None = None
        completed = 0
        pending = set(tasks)

        # Process agents as they complete (FIRST_COMPLETED loop)
        while pending:
            done, pending = await asyncio.wait(
                pending,
                timeout=timeout_s - (time.time() - start),
                return_when=asyncio.FIRST_COMPLETED,
            )

            if not done:
                log.warning("[Swarm] Timeout — %d agent(s) cancelled", len(pending))
                break

            for task in done:
                completed += 1
                try:
                    result: AgentResult = task.result()
                except Exception as exc:
                    log.error("[Swarm] Task raised: %s", exc)
                    continue

                yield {
                    "type": "partial",
                    "agent": result.agent_name,
                    "content": result.content,
                    "score": result.score,
                    "latency_ms": result.latency_ms,
                    "degraded": result.degraded,
                }

                if best is None or result.score > best.score:
                    best = result
                    yield {
                        "type": "best_update",
                        "content": result.content,
                        "score": result.score,
                        "agent": result.agent_name,
                    }
                    log.info("[Swarm] Best updated → %s (score=%.3f)", result.agent_name, result.score)

                # Early exit check
                elapsed_frac = (time.time() - start) / timeout_s
                if result.score >= _EARLY_EXIT_THRESHOLD and elapsed_frac < _EARLY_EXIT_WINDOW:
                    log.info(
                        "[Swarm] Early exit triggered by '%s' (score=%.3f, %.0f%% time used)",
                        result.agent_name,
                        result.score,
                        elapsed_frac * 100,
                    )
                    pending = set()
                    break

        # Cancel anything still running
        for task in pending:
            task.cancel()

        final = best or AgentResult(
            agent_name="fallback",
            content="No strong result within timeout — returning best effort.",
            score=0.40,
            latency_ms=round((time.time() - start) * 1000, 1),
        )

        yield {
            "type": "complete",
            "best_agent": final.agent_name,
            "final_answer": final.content,
            "confidence": round(final.score, 4),
            "agents_completed": completed,
            "total_latency_ms": round((time.time() - start) * 1000, 1),
        }

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    async def _run_agent_resilient(self, agent: Any, query: str, tenant_id: str, name: str) -> AgentResult:
        @SwarmResilience.retry_async(max_attempts=3)
        @SwarmResilience.circuit_breaker(fail_max=5)
        async def _wrapped():
            async def primary():
                return await agent.run(query, tenant_id)

            async def fallback():
                return await agent.run_with_secondary_provider(query, tenant_id)

            return await GenAIFallback.call_llm_with_fallback(primary(), fallback(), name)

        try:
            result = await SwarmResilience.run_with_resilience(
                _wrapped(), task_name=f"agent_{name}", metrics=self.task_metrics, timeout_seconds=45.0
            )
            # Handle both direct and FallbackResult objects
            data = result.data if isinstance(result, FallbackResult) else result
            score = self._score(data, name)
            return AgentResult(
                agent_name=name,
                content=data.get("content", ""),
                score=score,
                latency_ms=self.task_metrics[f"agent_{name}"]["latency_ms"],
                evidence=data.get("evidence", []),
                degraded=getattr(result, "degraded", False),
            )
        except Exception as exc:
            log.warning("[Swarm] Agent '%s' failed resilient execution: %s", name, exc)
            return AgentResult(agent_name=name, content=f"Agent failed: {exc}", score=0.30, latency_ms=0.0)

    @staticmethod
    def _score(result: dict, agent_name: str) -> float:
        base = float(result.get("confidence", 0.60))
        boost = {"vector": 0.08, "graph": 0.18, "simulation": 0.28}.get(agent_name, 0.0)
        return round(min(0.98, base + boost), 4)
