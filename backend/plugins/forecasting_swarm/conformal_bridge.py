"""Conformal bridge — adaptive interval calibration using ML inference data."""

from __future__ import annotations

import math

import numpy as np

from backend.app.core.supabase import get_supabase_client

MIN_CALIBRATION_SIZE = 30
TABLE_NAME = "conformal_calibration"


class ConformalBridge:
    def __init__(self, coverage: float = 0.90):
        self.coverage = coverage
        self._alpha = 1.0 - coverage
        self._cal_scores: list[float] = []
        self._supabase = get_supabase_client()

    def load_from_supabase(self, category: str | None = None, limit: int = 2000) -> int:
        self._cal_scores = []
        sb = self._supabase
        if sb is None:
            return 0

        query = sb.table(TABLE_NAME).select("calibration_score")
        if category:
            query = query.eq("category", category)
        query = query.order("created_at", desc=True).limit(limit)

        try:
            result = query.execute()
            if result.data:
                self._cal_scores = [float(r["calibration_score"]) for r in result.data]
        except Exception:
            pass

        if len(self._cal_scores) < MIN_CALIBRATION_SIZE:
            obs = _get_observability()
            if obs:
                obs.get_gauge("ml_inference_confidence_p95")
            return 0

        return len(self._cal_scores)

    def get_interval(self, point_estimate: float, coverage: float | None = None) -> tuple[float, float]:
        alpha = self._alpha if coverage is None else (1.0 - coverage)

        if len(self._cal_scores) < MIN_CALIBRATION_SIZE:
            fallback = max(0.08, float(np.std(self._cal_scores or [0.15]) * 2))
            lo = float(np.clip(point_estimate - fallback, 0.0, 1.0))
            hi = float(np.clip(point_estimate + fallback, 0.0, 1.0))
            return (lo, hi)

        n = len(self._cal_scores)
        q_level = math.ceil((n + 1) * (1 - alpha)) / n
        q_level = min(q_level, 1.0)
        q = float(np.quantile(sorted(self._cal_scores), q_level))

        lo = float(np.clip(point_estimate - q, 0.0, 1.0))
        hi = float(np.clip(point_estimate + q, 0.0, 1.0))
        return (lo, hi)

    def save_calibration_point(self, prediction: float, actual: float, category: str | None = None) -> None:
        score = abs(prediction - actual)
        self._cal_scores.append(score)

        sb = self._supabase
        if sb is None:
            return

        row = {"calibration_score": score, "category": category or "general"}
        try:
            sb.table(TABLE_NAME).insert(row).execute()
        except Exception:
            pass


_observability_instance = None


def _get_observability():
    global _observability_instance
    if _observability_instance is None:
        try:
            from backend.core.services.observability_service import observability

            _observability_instance = observability()
        except Exception:
            pass
    return _observability_instance
