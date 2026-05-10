"""Advanced regime-aware probabilistic forecasting engine for prediction markets."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from backend.core.agents.tournament import TournamentRuntime
from backend.core.probability.calibration import CalibrationEngine
from backend.core.probability.ensembles import BayesianModelCombination
from backend.core.probability.prediction import Prediction, Provenance
from backend.core.runtime.entity_graph.service import EntityGraphService
from backend.core.runtime.state_registry.service import StateRegistryService
from backend.core.runtime.temporal.engine import TemporalEngine
from backend.plugins.prediction_market.forecasting.signals import ForecastSignal


class ProbabilityEngine:
    def __init__(self) -> None:
        self._temporal = TemporalEngine()
        self._state_registry = StateRegistryService.registry()
        self._calibration = CalibrationEngine()
        self._bmc = BayesianModelCombination()
        self._tournament = TournamentRuntime()

    async def forecast(
        self,
        signals: list[ForecastSignal],
        market_context: dict[str, Any],
    ) -> Prediction:
        if not signals:
            return Prediction(
                value=0.5,
                confidence=0.3,
                uncertainty=0.4,
                provenance=[Provenance(source="fallback", weight=1.0)],
                metadata={"regime": "unknown"},
            )

        current_state = await self._state_registry.get_current()
        regime = getattr(current_state, "regime", "normal")

        decayed_signals = self._apply_signal_decay(signals, current_state.timestamp)

        graph_context: dict[str, Any] = {}
        try:
            graph_context = await EntityGraphService.graph().retrieve_context(
                query=(
                    market_context.get("title", "")
                    + " "
                    + market_context.get("description", "")
                ),
                category="prediction_market",
            )
        except Exception:
            graph_context = {"hop_count": 0}

        agent_predictions: list[dict[str, Any]] = []
        for signal in decayed_signals:
            agent_predictions.append(
                {
                    "prob": signal.value,
                    "confidence": signal.confidence,
                    "brier_weight": self._tournament.get_agent_weight(signal.source)
                    or 1.0,
                }
            )

        combined = self._bmc.aggregate(agent_predictions)

        uncertainty, breakdown = self._compute_regime_uncertainty(
            combined.get("probability", 0.5),
            combined.get("disagreement", 0.0),
            regime,
            graph_context,
        )

        calibrated_prob = self._calibration.calibrate(
            combined.get("probability", 0.5), regime
        )

        final_prediction = Prediction(
            value=calibrated_prob,
            confidence=max(0.1, 1.0 - uncertainty),
            uncertainty=uncertainty,
            provenance=[
                Provenance(
                    source=s.source,
                    weight=s.confidence,
                    metadata={"signal_id": s.id, "signal_type": s.signal_type},
                )
                for s in decayed_signals
            ]
            + [Provenance(source="bmc_ensemble", weight=1.0)],
            metadata={
                "engine_version": "v2_simplified_uncertainty",
                "disagreement": breakdown["disagreement"],
                "graph_hops": graph_context.get("hop_count", 0),
                "regime": regime,
                "uncertainty_breakdown": breakdown,
            },
        )

        self._tournament.record(
            agent_name="probability_engine",
            prediction=final_prediction.value,
            outcome=None,
        )

        return final_prediction

    def _apply_signal_decay(
        self,
        signals: list[ForecastSignal],
        now: datetime,
    ) -> list[ForecastSignal]:
        return [
            s
            for s in signals
            if self._temporal.decay_factor(s.timestamp, now, half_life_hours=12) > 0.15
        ]

    def _compute_regime_uncertainty(
        self,
        prob: float,
        disagreement: float,
        regime: str,
        graph_context: dict[str, Any],
    ) -> tuple[float, dict[str, Any]]:
        base = 0.12
        disagreement_factor = disagreement * 0.45
        graph_hops = graph_context.get("hop_count", 0)
        complexity_factor = min(0.18, graph_hops * 0.04)
        regime_multiplier = {"normal": 1.0, "panic": 1.65, "disruption": 2.1}.get(
            regime, 1.4
        )

        uncertainty = (
            base + disagreement_factor + complexity_factor
        ) * regime_multiplier
        uncertainty = max(0.15, min(0.68, uncertainty))

        breakdown = {
            "base": base,
            "disagreement": disagreement_factor,
            "complexity": complexity_factor,
            "regime_mult": regime_multiplier,
        }
        return uncertainty, breakdown


probability_engine = ProbabilityEngine()
