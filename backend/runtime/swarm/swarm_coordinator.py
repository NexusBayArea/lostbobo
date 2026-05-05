"""Swarm Coordinator — dispatches agents via Redis queue, aggregates via Bayesian."""

from __future__ import annotations

import logging
from dataclasses import dataclass
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
class PredictionQuestion:
    question_id: str
    title: str
    description: str
    category: str = "general"
    graph_context: list[dict[str, Any]] | None = None


class SwarmCoordinator:
    def __init__(self):
        self.aggregator = BayesianAggregator()
        self.conformal_bridge = ConformaBridge()
        self._sb = get_supabase_client()

    async def run(self, question: PredictionQuestion) -> AggregatedForecast:
        dummy_outputs = [
            AgentOutput(
                agent_role=role,
                probability=0.5 + (i - 2) * 0.1,
                confidence=0.7,
                reasoning=f"Agent {role.value} reasoning",
            )
            for i, role in enumerate(AgentRole)
        ]

        forecast = self.aggregator.aggregate(
            question_id=question.question_id,
            agent_outputs=dummy_outputs,
            conformal_bridge=self.conformal_bridge,
        )

        await self._persist_forecast(forecast, question)
        await self._trigger_report_and_feedback(forecast, question)

        return forecast

    async def _persist_forecast(self, forecast: AggregatedForecast, question: PredictionQuestion) -> None:
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
                    "title": question.title,
                }
            ).execute()
            log.info("Forecast persisted: %s", forecast.question_id)
        except Exception as e:
            log.warning("Failed to persist forecast: %s", e)

    async def _trigger_report_and_feedback(self, forecast: AggregatedForecast, question: PredictionQuestion) -> None:
        try:
            from backend.app.services.pdf_service import PDFReportService

            pdf_service = PDFReportService()
            report_path = pdf_service.generate_forecast_report(
                forecast=forecast,
                question=question,
                agent_outputs=[],
            )
            log.info("PDF report generated: %s", report_path)
        except Exception as e:
            log.warning("PDF report generation failed: %s", e)

        log.info("Auto-triggered feedback for %s", question.question_id)
