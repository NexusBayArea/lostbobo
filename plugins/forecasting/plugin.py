from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.core.sdk.abi.plugin_manifest import PluginManifest
from backend.core.sdk.base_plugin import BasePlugin


class ForecastingPlugin(BasePlugin):
    def __init__(self):
        manifest_path = Path(__file__).parent / "manifest.json"
        with open(manifest_path) as f:
            data = json.load(f)
        self.manifest = PluginManifest(**data)

    async def register(self, kernel: Any) -> None:
        kernel.capability_registry.register(
            "forecast.generate",
            self.forecast,
            plugin_name="forecasting",
            version="1.0.0",
            timeout_seconds=1800,
        )
        kernel.capability_registry.register(
            "forecast.calibrate",
            self.calibrate,
            plugin_name="forecasting",
            version="1.0.0",
        )
        kernel.capability_registry.register(
            "forecast.generate_prompt",
            self.generate_prompt,
            plugin_name="forecasting",
        )
        kernel.capability_registry.register(
            "forecast.capacity",
            self.capacity,
            plugin_name="forecasting",
            version="1.0.0",
            timeout_seconds=300,
        )

    async def forecast(self, payload: dict[str, Any]) -> dict[str, Any]:
        model = payload.get("model")
        model_payload = payload.get("payload", {})

        if model == "weather":
            from plugins.forecasting.models.weather.model import WeatherModel

            result = await WeatherModel().predict(model_payload)
        elif model == "ev":
            from plugins.forecasting.models.ev.model import EVModel

            result = await EVModel().predict(model_payload)
        elif model == "market":
            from plugins.forecasting.models.market.model import MarketModel

            result = await MarketModel().predict(model_payload)
        elif model == "wildfire":
            from plugins.forecasting.models.wildfire.model import WildfireModel

            result = await WildfireModel().predict(model_payload)
        else:
            raise ValueError(f"Unknown forecast model: {model}")

        return {
            "mean": result.mean,
            "confidence_interval": result.confidence_interval,
            "metadata": result.metadata,
        }

    async def calibrate(self, payload: dict[str, Any]) -> dict[str, Any]:
        model = payload.get("model")
        calibration_data = payload.get("data")
        return {
            "model": model,
            "calibrated": True,
            "samples": len(calibration_data or []),
        }

    async def generate_prompt(self, payload: dict[str, Any]) -> str:
        domain = payload.get("domain")
        template_name = payload.get("template", "default")
        prompt_path = (
            Path(__file__).parent / "prompts" / f"{domain}_{template_name}.txt"
        )
        if prompt_path.exists():
            return prompt_path.read_text()
        raise ValueError(
            f"Prompt not found for domain={domain}, template={template_name}"
        )

    async def capacity(self, payload: dict[str, Any]) -> dict[str, Any]:
        from plugins.forecasting.forecasting import get_capacity_forecaster

        forecaster = get_capacity_forecaster()
        horizon = payload.get("horizon", "15m")
        from plugins.forecasting.forecasting import ForecastHorizon

        return await forecaster.predict_demand(ForecastHorizon(horizon))


plugin = ForecastingPlugin()
