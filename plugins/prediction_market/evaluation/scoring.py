"""Evaluation — scoring, outcomes, replay, and leaderboard."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel



class ForecastOutcome(BaseModel):
    outcome_id: str
    market_id: str
    prediction_id: str
    predicted_value: float
    actual_outcome: float
    resolved_at: str
    brier_score: float


class ScoringEngine:
    async def score_prediction(
        self,
        predicted: float,
        actual: float,
    ) -> dict[str, float]:
        brier = (predicted - actual) ** 2
        accuracy = 1.0 - abs(predicted - actual)
        return {
            "brier_score": round(brier, 6),
            "accuracy": round(accuracy, 4),
            "direction_correct": (predicted > 0.5) == (actual > 0.5),
        }

    async def compute_leaderboard(
        self,
        forecasts: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        scored = []
        for f in forecasts:
            brier = (f.get("predicted", 0.5) - f.get("actual", 0.5)) ** 2
            scored.append(
                {
                    "participant": f.get("participant_id", "unknown"),
                    "brier_score": round(brier, 6),
                    "n_forecasts": f.get("n_forecasts", 1),
                    "rank": 0,
                }
            )

        scored.sort(key=lambda x: x["brier_score"])
        for i, s in enumerate(scored):
            s["rank"] = i + 1

        return scored


class OutcomeTracker:
    def __init__(self) -> None:
        self._outcomes: list[dict[str, Any]] = []

    async def record(
        self,
        market_id: str,
        prediction_id: str,
        predicted: float,
        actual: float,
    ) -> dict[str, Any]:
        brier = (predicted - actual) ** 2
        outcome = {
            "outcome_id": str(uuid4()),
            "market_id": market_id,
            "prediction_id": prediction_id,
            "predicted_value": predicted,
            "actual_outcome": actual,
            "brier_score": round(brier, 6),
            "resolved_at": datetime.now(UTC).isoformat(),
        }
        self._outcomes.append(outcome)
        return outcome

    async def get_recent(self, limit: int = 50) -> list[dict[str, Any]]:
        return sorted(
            self._outcomes,
            key=lambda x: x["resolved_at"],
            reverse=True,
        )[:limit]

    async def replay(
        self,
        market_id: str,
        forecasts: list[dict[str, Any]],
        actual: float,
    ) -> dict[str, Any]:
        results = []
        for f in forecasts:
            scored = await self.score_prediction(f.get("value", 0.5), actual)
            results.append({**f, **scored})

        results.sort(key=lambda x: x["brier_score"])
        return {
            "market_id": market_id,
            "actual_outcome": actual,
            "ranked_forecasts": results,
            "winner": results[0].get("participant_id") if results else None,
        }
