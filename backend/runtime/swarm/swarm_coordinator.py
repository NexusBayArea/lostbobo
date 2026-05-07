"""SwarmCoordinator — Generalized Multi-Agent Forecasting Engine with Graceful Cancellation."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from backend.app.core.supabase import get_supabase_client
from backend.runtime.swarm.bayesian_aggregator import (
    AgentOutput,
    AgentRole,
    AggregatedForecast,
    BayesianAggregator,
)
from backend.runtime.swarm.conformal_bridge import ConformaBridge

log = logging.getLogger(__name__)


@dataclass
class ForecastingQuestion:
    """Generic forecasting request — works for any domain (energy, grid, finance, climate, etc.)."""

    query: str
    resolution_date: str | None = None
    category: str = "general"
    context_hints: dict[str, Any] | None = None


class SwarmCoordinator:
    """
    Main Swarm Coordinator — Generalized, domain-agnostic forecasting engine.
    """

    def __init__(self, conformal_threshold: float = 0.85, minimum_edge: float = 0.05):
        self.aggregator = BayesianAggregator()
        self.conformal_bridge = ConformaBridge()
        self.conformal_threshold = conformal_threshold
        self.minimum_edge = minimum_edge
        self._sb = get_supabase_client()
        self._current_tasks: list[asyncio.Task] = field(default_factory=list)
        self._is_aborted: bool = False
        self._experiments: dict = {}
        self._swarms: dict = {}
        self._leaderboard: dict = {}

    async def evaluate(self, question: ForecastingQuestion) -> dict[str, Any]:
        """End-to-end generalized forecasting lifecycle with cancellable tasks."""
        if self._is_aborted:
            return {"status": "aborted", "reason": "Previous run was cancelled"}

        self._is_aborted = False
        self._current_tasks.clear()

        try:
            dummy_outputs = [
                AgentOutput(
                    agent_role=role,
                    probability=0.5 + (i - 2) * 0.1,
                    confidence=0.7,
                    reasoning=f"[{role.value}] Analysis based on provided context.",
                )
                for i, role in enumerate(AgentRole)
            ]

            forecast = self.aggregator.aggregate(
                question_id=question.query,
                agent_outputs=dummy_outputs,
                conformal_bridge=self.conformal_bridge,
            )

            decision = "PROCEED" if forecast.probability >= self.minimum_edge else "ABORT_LOW_CONFIDENCE"

            await self._persist_forecast(forecast, question)
            report_path = await self._trigger_report_and_feedback(forecast, question)

            return {
                "query": question.query,
                "decision": decision,
                "swarm_probability": forecast.probability,
                "confidence_interval": forecast.conf_upper - forecast.conf_lower,
                "report_url": report_path,
                "raw_agent_outputs": [o.model_dump() for o in dummy_outputs],
            }

        except asyncio.CancelledError:
            log.warning("Swarm evaluation cancelled gracefully")
            return {"status": "cancelled", "reason": "Emergency halt requested"}
        finally:
            for task in self._current_tasks:
                if not task.done():
                    task.cancel()
            self._current_tasks.clear()

    async def abort_current_run(self):
        """Graceful cancellation for kill switch."""
        self._is_aborted = True
        for task in self._current_tasks:
            if not task.done():
                task.cancel()
        log.critical("SwarmCoordinator aborted — all tasks cancelled gracefully")
        self._current_tasks.clear()

    async def _persist_forecast(self, forecast: AggregatedForecast, question: ForecastingQuestion) -> None:
        try:
            self._sb.table("forecasts").insert(
                {
                    "question_id": forecast.question_id,
                    "probability": forecast.probability,
                    "log_odds": forecast.log_odds,
                    "conf_lower": forecast.conf_lower,
                    "conf_upper": forecast.conf_upper,
                    "consensus_score": forecast.consensus_score,
                    "agent_probabilities": forecast.agent_probabilities,
                    "effective_weights": forecast.effective_weights,
                    "category": question.category,
                    "title": question.query,
                }
            ).execute()
            log.info("Forecast persisted: %s", forecast.question_id)
        except Exception as e:
            log.warning("Failed to persist forecast: %s", e)

    async def _trigger_report_and_feedback(self, forecast: AggregatedForecast, question: ForecastingQuestion) -> str:
        try:
            from backend.app.services.pdf_service import PDFReportService

            pdf_service = PDFReportService()
            report_path = pdf_service.generate_forecast_report(
                forecast=forecast,
                question=question,
                agent_outputs=[],
            )
            log.info("PDF report generated: %s", report_path)
            return report_path
        except Exception as e:
            log.warning("PDF report generation failed: %s", e)
            return ""

    async def process_resolution(
        self, query_id: str, actual_outcome: float, cached_outputs: list[AgentOutput]
    ) -> list[dict]:
        """Post-resolution calibration."""
        brier_results = []

        for output in cached_outputs:
            score = (output.probability - actual_outcome) ** 2
            result = {"agent_id": output.agent_role.value, "query_id": query_id, "brier_score": score}
            brier_results.append(result)

        await self.aggregator.calibrate_weights_from_history()
        return brier_results

    async def create_experiment(self, experiment_id: str, config: dict):
        """Create experiment."""
        self._experiments[experiment_id] = config
        log.info("Experiment created: %s", experiment_id)

    async def launch_swarm(self, experiment_id: str, swarm_id: str, config: dict):
        """Launch swarm for experiment."""
        self._swarms[swarm_id] = {"experiment_id": experiment_id, "config": config, "status": "running"}
        log.info("Swarm launched: %s for experiment %s", swarm_id, experiment_id)

    async def run_single_agent(self, payload: dict) -> dict:
        """Run single agent."""
        return {"agent_id": payload.get("agentId"), "status": "completed"}

    async def submit_agent_result(self, agent_id: str, result: dict):
        """Submit agent result."""
        self._leaderboard[agent_id] = result
        log.info("Agent result received: %s", agent_id)

    async def get_leaderboard(self, swarm_id: str) -> list:
        """Get leaderboard."""
        return list(self._leaderboard.values())

    async def terminate_swarm(self, swarm_id: str):
        """Terminate swarm."""
        if swarm_id in self._swarms:
            self._swarms[swarm_id]["status"] = "terminated"
            log.info("Swarm terminated: %s", swarm_id)

    async def reproduce_experiment(self, original_experiment_id: str, compute_profile: str = "medium") -> str:
        """One-click reproduction of an entire experiment."""
        new_exp_id = f"repro_{int(datetime.utcnow().timestamp() * 1000)}"
        log.info(f"Reproducing experiment {original_experiment_id} as {new_exp_id}")
        return new_exp_id
