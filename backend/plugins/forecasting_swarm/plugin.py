"""Forecasting Swarm Plugin — Bayesian agent-based probabilistic forecasting."""

from backend.plugins.base import PluginBase
from backend.plugins.registry import PluginRegistry


@PluginRegistry.register("forecasting_swarm")
class ForecastingSwarmPlugin(PluginBase):
    name = "forecasting_swarm"
    version = "0.1.0"
    category = "forecasting"
    description = (
        "Bayesian agent swarm for probabilistic forecasting with conformal calibration and consensus aggregation"
    )

    async def run(self, input_data: dict) -> dict:
        from backend.plugins.forecasting_swarm.swarmer import SwarmRunner

        runner = SwarmRunner()
        result = await runner.run_from_dict(input_data)
        return result

    async def validate_input(self, input_data: dict) -> bool:
        return "question" in input_data or "question_id" in input_data
