"""Bayesian log-odds aggregation with consensus + dissent detection."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np

from backend.plugins.forecasting_swarm.models import (
    AgentOutput,
    AggregatedForecast,
)

if TYPE_CHECKING:
    from backend.plugins.forecasting_swarm.conformal_bridge import ConformalBridge


class BayesianAggregator:
    DISSENT_THRESHOLD = 0.15

    def __init__(self, coverage: float = 0.90):
        self.coverage = coverage

    def aggregate(
        self,
        question_id: str,
        agent_outputs: list[AgentOutput],
        conformal_bridge: ConformalBridge,
    ) -> AggregatedForecast:
        if not agent_outputs:
            return AggregatedForecast(
                question_id=question_id,
                final_estimate=0.5,
                confidence_interval=(0.0, 1.0),
                consensus_score=0.0,
                dissent_detected=False,
                agent_count=0,
            )

        weights = np.array([max(o.weight, 0.001) for o in agent_outputs])
        weights = weights / weights.sum()

        log_odds_estimates = [
            math.log(max(p, 1e-9) / (1 - max(p, 1e-9))) for p in [o.point_estimate for o in agent_outputs]
        ]
        weighted_log_odds = np.sum(weights * np.array(log_odds_estimates))
        bmc = 1.0 / (1.0 + math.exp(-weighted_log_odds))

        ci_lo_list, ci_hi_list = [], []
        for out in agent_outputs:
            ci_lo_list.append(out.confidence_interval[0])
            ci_hi_list.append(out.confidence_interval[1])

        avg_ci_lo = float(np.mean(ci_lo_list))
        avg_ci_hi = float(np.mean(ci_hi_list))
        conformal_lo, conformal_hi = conformal_bridge.get_interval(bmc)

        ci_lo = max(avg_ci_lo, conformal_lo)
        ci_hi = min(avg_ci_hi, conformal_hi)

        predictions = np.array([o.point_estimate for o in agent_outputs])
        mean_pred = float(np.mean(predictions))
        std_pred = float(np.std(predictions))

        consensus_score = float(1.0 / (1.0 + std_pred * 10))
        model_diversity = float(np.std(weights * predictions) / (np.mean(predictions) + 1e-9))

        dissenting = []
        for out in agent_outputs:
            deviation = abs(out.point_estimate - mean_pred)
            if deviation > self.DISSENT_THRESHOLD:
                dissenting.append(out.agent_id)

        cal_coverages = [o.calibration_score for o in agent_outputs]

        return AggregatedForecast(
            question_id=question_id,
            final_estimate=round(float(np.clip(bmc, 0.0, 1.0)), 4),
            confidence_interval=(round(ci_lo, 4), round(ci_hi, 4)),
            consensus_score=round(consensus_score, 4),
            dissent_detected=len(dissenting) > 0,
            dissenting_agents=dissenting,
            agent_count=len(agent_outputs),
            calibration_coverages=[round(c, 4) for c in cal_coverages],
            metadata={
                "bmc_raw": round(weighted_log_odds, 4),
                "model_diversity": round(model_diversity, 4),
                "std_predictions": round(std_pred, 4),
            },
        )
