"""Simulation Retrieval Agent — highest-trust path grounded in past simulation runs."""

from __future__ import annotations

import logging

from backend.runtime.rag.router import RAGRouter

log = logging.getLogger(__name__)


class SimulationRetrievalAgent:
    """
    Retrieves and ranks previously executed simulation results that match
    the query's physical parameters.  Highest trust tier because evidence
    is deterministic and reproducible.
    """

    def __init__(self) -> None:
        self._router = RAGRouter()

    async def run(self, query: str, tenant_id: str = "public") -> dict:
        try:
            # Pull broad context; experiment_index results will contain run metadata
            context = await self._router.retrieve(query, tenant_id=tenant_id, top_k=10)

            # Filter to items that look like simulation runs (have run_id or sim_hash)
            sim_results = [
                item
                for item in context
                if item.get("run_id") or item.get("sim_hash") or item.get("layer") == "experiment"
            ]

            if sim_results:
                top = sim_results[0]
                snippet = top.get("text", top.get("summary", ""))[:300]
                confidence = 0.88
            else:
                # Graceful fallback — still useful but lower confidence
                top = context[0] if context else {}
                snippet = top.get("text", "No prior simulation found for this query.")[:300]
                confidence = 0.55

            return {
                "content": (
                    f"Simulation evidence ({len(sim_results)} matching runs): "
                    f"{snippet}{'...' if len(snippet) == 300 else ''}"
                ),
                "confidence": confidence,
                "evidence": sim_results[:3] or context[:3],
                "simulation_hits": len(sim_results),
            }
        except Exception as exc:
            log.warning("SimulationRetrievalAgent.run failed: %s", exc)
            return {"content": f"Simulation agent error: {exc}", "confidence": 0.2, "evidence": []}
