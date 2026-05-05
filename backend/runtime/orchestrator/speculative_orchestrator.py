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
from backend.runtime.rag.router import RAGRouter

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


class SpeculativeOrchestrator:
    """
    Runs multiple reasoning paths in parallel (vector, graph, simulation).

    Behaviour:
    - Streams a ``partial`` event the moment each agent returns.
    - Emits a ``best_update`` event whenever the incumbent best answer changes.
    - Applies early-exit: if one agent exceeds the confidence threshold within
      the first 70 % of the timeout window, all slower branches are cancelled.
    - Always emits a final ``complete`` event.
    """

    def __init__(self) -> None:
        self.rag_router = RAGRouter()
        self.vector_agent = VectorRAGAgent()
        self.graph_agent = GraphRAGAgent()
        self.sim_agent = SimulationRetrievalAgent()

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

        Yields dicts with a ``type`` key:
          - ``start``       — query received
          - ``partial``     — one agent finished
          - ``best_update`` — incumbent answer improved
          - ``complete``    — final answer selected
        """
        start = time.time()
        timeout_s = timeout_ms / 1000.0

        yield {"type": "start", "query": query}
        log.info("[Swarm] Starting speculative query: %s", query)

        tasks: list[asyncio.Task] = [
            asyncio.create_task(
                self._run_agent(self.vector_agent, query, tenant_id, "vector"),
                name="agent_vector",
            ),
            asyncio.create_task(
                self._run_agent(self.graph_agent, query, tenant_id, "graph"),
                name="agent_graph",
            ),
            asyncio.create_task(
                self._run_agent(self.sim_agent, query, tenant_id, "simulation"),
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
                # Timeout expired before any remaining task finished
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
                    pending = set()  # signal outer while to break
                    break

        # Cancel anything still running
        for task in pending:
            task.cancel()
            log.debug("[Swarm] Cancelled task: %s", task.get_name())

        # Synthesise final answer
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
        log.info(
            "[Swarm] Complete — best=%s confidence=%.3f latency=%.0fms",
            final.agent_name,
            final.score,
            (time.time() - start) * 1000,
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    async def _run_agent(self, agent: Any, query: str, tenant_id: str, name: str) -> AgentResult:
        t0 = time.time()
        try:
            result = await agent.run(query, tenant_id)
            latency = (time.time() - t0) * 1000
            score = self._score(result, name)
            log.debug("[Swarm] Agent '%s' done in %.0fms, score=%.3f", name, latency, score)
            return AgentResult(
                agent_name=name,
                content=result.get("content", ""),
                score=score,
                latency_ms=round(latency, 1),
                evidence=result.get("evidence", []),
            )
        except Exception as exc:
            latency = (time.time() - t0) * 1000
            log.warning("[Swarm] Agent '%s' failed in %.0fms: %s", name, latency, exc)
            return AgentResult(
                agent_name=name,
                content=f"Agent failed: {exc}",
                score=0.30,
                latency_ms=round(latency, 1),
            )

    @staticmethod
    def _score(result: dict, agent_name: str) -> float:
        """
        Blend the agent's self-reported confidence with a trust prior per tier.
        Simulation evidence is highest trust; vector is fastest but shallowest.
        """
        base = float(result.get("confidence", 0.60))
        boost = {
            "vector": 0.08,
            "graph": 0.18,
            "simulation": 0.28,
        }.get(agent_name, 0.0)
        return round(min(0.98, base + boost), 4)
