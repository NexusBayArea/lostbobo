"""Main entry point for the forecasting swarm plugin."""

from __future__ import annotations

import logging
from typing import Any

from backend.plugins.forecasting_swarm.conformal_bridge import ConformalBridge
from backend.plugins.forecasting_swarm.models import PredictionQuestion
from backend.plugins.forecasting_swarm.swarm_coordinator import SwarmCoordinator

logger = logging.getLogger(__name__)


class SwarmRunner:
    def __init__(self, coverage: float = 0.90):
        self.coordinator = SwarmCoordinator(coverage=coverage)

    async def run_from_dict(self, input_data: dict[str, Any]) -> dict[str, Any]:
        question = PredictionQuestion(
            question_id=input_data.get("question_id"),
            question_text=input_data["question"],
            resolution_criteria=input_data.get("resolution_criteria", ""),
            category=input_data.get("category", "general"),
            time_horizon_days=input_data.get("time_horizon_days", 30),
            background_context=input_data.get("background_context", ""),
        )

        forecast = await self.coordinator.run(question)

        return {
            "question_id": forecast.question_id,
            "final_estimate": forecast.final_estimate,
            "confidence_interval": forecast.confidence_interval,
            "consensus_score": forecast.consensus_score,
            "dissent_detected": forecast.dissent_detected,
            "dissenting_agents": forecast.dissenting_agents,
            "agent_count": forecast.agent_count,
            "calibration_coverages": forecast.calibration_coverages,
            "metadata": forecast.metadata,
        }

    def calibrate_on_resolution(self, question_id: str, actual_outcome: float) -> None:
        bridge = ConformalBridge()
        if hasattr(self.coordinator, "_last_prediction"):
            pred = self.coordinator._last_prediction
            bridge.save_calibration_point(pred, actual_outcome)
