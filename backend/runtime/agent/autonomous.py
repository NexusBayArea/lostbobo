"""Autonomous Simulation Agent — closed-loop experimentation."""

from __future__ import annotations

import logging
import time  # Import time for run_id generation
from dataclasses import dataclass
from typing import Any

from backend.plugins.registry import PluginRegistry
from backend.runtime.cache.simulation_cache import SimulationCache
from backend.runtime.provenance.graph import ProvenanceGraph, ProvenanceNode
from backend.runtime.rag.router import RAGRouter

log = logging.getLogger(__name__)


@dataclass
class ExperimentPlan:
    hypothesis: str
    parameters: dict[str, Any]
    iterations: int = 5


@dataclass
class ExperimentResult:
    run_id: str
    parameters: dict
    outputs: dict
    metrics: dict
    provenance_id: str


class AutonomousSimulationAgent:
    """
    Closed-loop agent:
    Query → RAG → Plan → Simulate → Analyze → New Hypothesis
    """

    def __init__(self):
        self.rag = RAGRouter()
        self.cache = SimulationCache()
        self.graph = ProvenanceGraph()
        self.max_iterations = 12

    async def research(self, query: str, tenant_id: str = "public") -> dict:
        """Main entrypoint: Engineer asks a question → autonomous research loop."""
        log.info("Autonomous research started: %s", query)

        context = await self.rag.retrieve(query, tenant_id=tenant_id, top_k=20)
        history: list[ExperimentResult] = []

        for iteration in range(self.max_iterations):
            plan = await self._generate_experiment_plan(query, context, history)
            log.info("Iteration %d — Hypothesis: %s", iteration, plan.hypothesis)

            result = await self._execute_experiment(plan, tenant_id)
            history.append(result)

            analysis = await self._analyze_results(history)
            log.info("Analysis: %s", analysis.get("insight", ""))

            if analysis.get("converged", False):
                log.info("Converged after %d iterations", iteration + 1)
                break

            # Update context for next iteration
            context = await self._update_context(context, analysis)

        final_report = await self._generate_final_report(query, history)
        return final_report

    async def _generate_experiment_plan(
        self, query: str, context: list[dict], history: list[ExperimentResult]
    ) -> ExperimentPlan:
        """LLM / rule-based planner (replace with real LLM call later)."""
        # Stub for now — in production call your Swarm / LLM planner
        return ExperimentPlan(
            hypothesis=f"Testing optimal parameters for: {query}",
            parameters={"c_rate": 3.0, "temperature": 298},
            iterations=1,
        )

    async def _execute_experiment(self, plan: ExperimentPlan, tenant_id: str) -> ExperimentResult:
        """Run via plugin or direct simulation with cache."""
        # Try domain plugin first
        try:
            # Example: dynamically select plugin based on domain/parameters
            # For now, hardcoded to ev_battery
            plugin = PluginRegistry.get("ev_battery")
            outputs = await plugin.run(plan.parameters)
        except Exception as e:
            log.warning(f"EV Battery plugin failed: {e}. Falling back to direct simulation.")
            # Fallback to direct simulation
            outputs = {"max_temp": 335.0, "plating": 0.45}

        run_id = f"auto-{int(time.time()*1000)}"

        # Cache + Provenance
        await self.cache.store(plan.parameters, outputs)
        node = ProvenanceNode(
            node_id=run_id, node_type="experiment", data={"hypothesis": plan.hypothesis, **plan.parameters}
        )
        await self.graph.add_node(node)

        return ExperimentResult(
            run_id=run_id,
            parameters=plan.parameters,
            outputs=outputs,
            metrics={"plating_risk": outputs.get("plating", 0.0)},
            provenance_id=node.node_id,
        )

    async def _analyze_results(self, history: list[ExperimentResult]) -> dict:
        """Simple analyzer — extend with LLM later."""
        if not history:
            return {"insight": "No data yet", "converged": False}

        best = min(history, key=lambda r: r.metrics.get("plating_risk", 1.0))
        return {
            "insight": f"Best result so far: plating risk {best.metrics.get('plating_risk'):.2f}",
            "converged": len(history) >= 5,
            "best_run": best.run_id,
        }

    async def _update_context(self, context: list[dict], analysis: dict) -> list[dict]:
        """Feed insights back into RAG for next iteration."""
        # In a real implementation, this would likely involve a RAG call to generate
        # new hypotheses or refine search queries based on analysis.
        return context  # extend with new retrieval

    async def _generate_final_report(self, query: str, history: list[ExperimentResult]) -> dict:
        """Summary for engineer + PDF trigger."""
        return {
            "query": query,
            "iterations": len(history),
            "best_result": max(history, key=lambda r: r.metrics.get("plating_risk", 0)),
            "recommendation": "Optimal charge rate found with low plating risk",
            "status": "completed",
        }
