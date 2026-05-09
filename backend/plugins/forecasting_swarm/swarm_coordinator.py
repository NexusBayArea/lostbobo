"""Swarm coordinator — orchestrates parallel agent execution with tracing + observability."""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass

from backend.core.services.observability_service import observability
from backend.core.services.tracing import tracer
from backend.plugins.forecasting_swarm.bayesian_aggregator import BayesianAggregator
from backend.plugins.forecasting_swarm.conformal_bridge import ConformalBridge
from backend.plugins.forecasting_swarm.models import (
    AgentOutput,
    AgentRole,
    AggregatedForecast,
    PredictionQuestion,
)

logger = logging.getLogger(__name__)


@dataclass
class AgentNode:
    role: AgentRole
    question: PredictionQuestion
    calibration_score: float = 0.5


class SwarmCoordinator:
    def __init__(self, coverage: float = 0.90):
        self.coverage = coverage
        self.aggregator = BayesianAggregator(coverage=coverage)
        self.conformal_bridge = ConformalBridge(coverage=coverage)
        self.conformal_bridge.load_from_supabase()

    async def run(
        self,
        question: PredictionQuestion,
        trace_id: str | None = None,
    ) -> AggregatedForecast:
        with tracer.start_as_current_span(
            "forecast.swarm",
            attributes={
                "question_id": question.question_id,
                "category": question.category,
                "time_horizon_days": question.time_horizon_days,
            },
        ):
            obs = observability()
            obs.increment("swarm_runs_total", {"category": question.category})

            start = time.time()
            nodes = self._build_nodes(question)
            agent_outputs = await self._run_agents_parallel(nodes)
            elapsed = time.time() - start

            forecast = self.aggregator.aggregate(question.question_id, agent_outputs, self.conformal_bridge)

            obs.gauge("swarm_consensus_score", forecast.consensus_score)
            obs.gauge("swarm_dissent_rate", float(len(forecast.dissenting_agents) / max(1, forecast.agent_count)))
            obs.observe("swarm_latency_ms", elapsed, {"category": question.category})

            return forecast

    def _build_nodes(self, question: PredictionQuestion) -> list[AgentNode]:
        roles = question.relevant_agents or [r for r in AgentRole]
        return [AgentNode(role=r, question=question) for r in roles]

    async def _run_agents_parallel(self, nodes: list[AgentNode]) -> list[AgentOutput]:
        tasks = [self._run_agent(node) for node in nodes]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        outputs = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning("Agent %s failed: %s", nodes[i].role, result)
            else:
                outputs.append(result)
        return outputs

    async def _run_agent(self, node: AgentNode) -> AgentOutput:
        with tracer.start_as_current_span(
            f"forecast.agent.{node.role.value}",
            attributes={"role": node.role.value, "question_id": node.question.question_id},
        ):
            est, reasoning = await self._simulate_agent_reasoning(node)

            obs = observability()
            obs.increment("swarm_agents_run", {"role": node.role.value})

            lo, hi = self.conformal_bridge.get_interval(est)

            return AgentOutput(
                agent_id=str(uuid.uuid4()),
                role=node.role,
                point_estimate=est,
                confidence_interval=(lo, hi),
                weight=self._role_weight(node.role),
                reasoning_summary=reasoning,
                calibration_score=node.calibration_score,
                novelty_score=0.5,
            )

    async def _simulate_agent_reasoning(self, node: AgentNode) -> tuple[float, str]:
        await asyncio.sleep(0.01)
        role_baselines = {
            AgentRole.TREND: 0.52,
            AgentRole.STRUCTURAL: 0.55,
            AgentRole.DISTRIBUTIONAL: 0.50,
            AgentRole.CONTRARIAN: 0.48,
        }
        base = role_baselines.get(node.role, 0.50)
        import random

        est = max(0.01, min(0.99, base + random.uniform(-0.08, 0.08)))
        reasoning = f"{node.role.value.title()} analysis of: {node.question.question_text[:80]}"
        return (round(est, 4), reasoning)

    def _role_weight(self, role: AgentRole) -> float:
        weights = {
            AgentRole.TREND: 0.30,
            AgentRole.STRUCTURAL: 0.35,
            AgentRole.DISTRIBUTIONAL: 0.25,
            AgentRole.CONTRARIAN: 0.10,
        }
        return weights.get(role, 0.25)
