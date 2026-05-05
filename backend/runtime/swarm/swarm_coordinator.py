"""Swarm Coordinator — runs 5 agents in parallel then aggregates."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

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

    async def run(self, question: PredictionQuestion) -> AggregatedForecast:
        """Run full swarm (stub agents for now — replace with real LLM calls)."""
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

        try:
            from backend.app.services.pdf_service import PDFReportService

            pdf_service = PDFReportService()
            report_path = pdf_service.generate_forecast_report(
                forecast=forecast,
                question=question,
                agent_outputs=dummy_outputs,
            )
            log.info("PDF report generated: %s", report_path)
        except Exception as e:
            log.warning("PDF report generation failed: %s", e)

        return forecast