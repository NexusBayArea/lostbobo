"""Brier scoring engine — runs after resolution. Supabase-only writes."""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass

import numpy as np

from backend.app.core.supabase import get_supabase_client

log = logging.getLogger(__name__)

EMA_ALPHA = 0.15
BRIER_COIN_FLIP = 0.25
DEFAULT_WEIGHT = 1.0
MIN_WEIGHT = 0.01
MAX_WEIGHT = 3.0


@dataclass
class AgentBrierResult:
    agent_role: str
    probability: float
    brier_score: float
    old_weight: float
    new_weight: float
    performance: float


@dataclass
class FeedbackResult:
    question_id: str
    actual_outcome: float
    ensemble_brier: float
    agent_results: list[AgentBrierResult]
    weights_updated: bool
    conformal_updated: bool
    graph_edges_added: int
    sha256_seal: str
    duration_ms: float


class BrierEngine:
    def __init__(self):
        self._sb = get_supabase_client()

    async def process(self, event) -> FeedbackResult:
        t0 = time.time()

        forecast = await self._load_forecast(event.question_id)
        if not forecast:
            return self._empty_result(event, time.time() - t0)

        ensemble_prob = float(forecast.get("probability", 0.5))
        agent_probs = forecast.get("agent_probabilities", {})
        category = event.get("category", "general")

        ensemble_brier = self._brier(ensemble_prob, event.actual_outcome)
        agent_results = await self._score_agents(agent_probs, event.actual_outcome, category)

        conformal_ok = await self._update_conformal(ensemble_prob, event.actual_outcome, event.question_id, category)
        edges_added = await self._enrich_graph(event, forecast, agent_results)

        seal = self._seal(event, ensemble_brier, agent_results)
        await self._persist_result(event, ensemble_brier, agent_results, seal)

        return FeedbackResult(
            question_id=event.question_id,
            actual_outcome=event.actual_outcome,
            ensemble_brier=ensemble_brier,
            agent_results=agent_results,
            weights_updated=True,
            conformal_updated=conformal_ok,
            graph_edges_added=edges_added,
            sha256_seal=seal,
            duration_ms=round((time.time() - t0) * 1000, 1),
        )

    async def _load_forecast(self, question_id: str) -> dict | None:
        try:
            resp = self._sb.table("forecasts").select("*").eq("question_id", question_id).execute()
            return resp.data[0] if resp.data else None
        except Exception as e:
            log.warning("Failed to load forecast: %s", e)
            return None

    async def _score_agents(self, agent_probs: dict, actual_outcome: float, category: str) -> list[AgentBrierResult]:
        results = []
        for role, prob in agent_probs.items():
            old_weight = 1.0
            score = self._brier(prob, actual_outcome)
            perf = performance(score)
            new_weight = np.clip(DEFAULT_WEIGHT * (1 + EMA_ALPHA * (perf - 0.5)), MIN_WEIGHT, MAX_WEIGHT)
            results.append(AgentBrierResult(role, prob, score, old_weight, new_weight, perf))
        return results

    async def _update_conformal(self, predicted: float, actual: float, question_id: str, category: str) -> bool:
        try:
            score = abs(predicted - actual)
            self._sb.table("conformal_calibration").insert(
                {
                    "question_id": question_id,
                    "predicted": predicted,
                    "actual": actual,
                    "score": score,
                    "category": category,
                }
            ).execute()
            return True
        except Exception as e:
            log.warning("Failed to update conformal: %s", e)
            return False

    async def _enrich_graph(self, event, forecast: dict, agent_results: list[AgentBrierResult]) -> int:
        edges_added = 0
        try:
            for ar in agent_results:
                self._sb.table("graph_edges").insert(
                    {
                        "source": f"agent:{ar.agent_role}",
                        "target": f"question:{event.question_id}",
                        "weight": ar.performance,
                        "category": "feedback",
                    }
                ).execute()
                edges_added += 1
        except Exception as e:
            log.warning("Failed to enrich graph: %s", e)
        return edges_added

    def _seal(self, event, ensemble_brier: float, agent_results: list[AgentBrierResult]) -> str:
        data = {
            "question_id": event.question_id,
            "actual_outcome": event.actual_outcome,
            "ensemble_brier": ensemble_brier,
            "agent_scores": [(ar.agent_role, ar.brier_score) for ar in agent_results],
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]

    async def _persist_result(
        self, event, ensemble_brier: float, agent_results: list[AgentBrierResult], seal: str
    ) -> None:
        try:
            self._sb.table("feedback_results").insert(
                {
                    "question_id": event.question_id,
                    "actual_outcome": event.actual_outcome,
                    "ensemble_brier": ensemble_brier,
                    "sha256_seal": seal,
                }
            ).execute()
        except Exception as e:
            log.warning("Failed to persist result: %s", e)

    def _brier(self, predicted: float, actual: float) -> float:
        return round((predicted - actual) ** 2, 6)

    def _empty_result(self, event, duration: float) -> FeedbackResult:
        return FeedbackResult(
            question_id=getattr(event, "question_id", "unknown"),
            actual_outcome=getattr(event, "actual_outcome", 0.0),
            ensemble_brier=0.25,
            agent_results=[],
            weights_updated=False,
            conformal_updated=False,
            graph_edges_added=0,
            sha256_seal="no_forecast",
            duration_ms=round(duration * 1000, 1),
        )


def brier(predicted: float, actual: float) -> float:
    return round((predicted - actual) ** 2, 6)


def performance(brier_score: float) -> float:
    return round(max(0.0, 1.0 - brier_score / BRIER_COIN_FLIP), 6)
