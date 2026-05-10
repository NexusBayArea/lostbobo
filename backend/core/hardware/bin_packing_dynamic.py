"""Dynamic heuristic selection — context-aware bin packing intelligence."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from backend.core.hardware.bin_packing import (
    AdvancedGPUBinPacker,
    BinPackingHeuristic,
)
from backend.core.hardware.pools import ExecutionCapacity
from backend.hardware.scheduler import SchedulingRequest


@dataclass
class HeuristicPerformanceRecord:
    success_rate: dict[BinPackingHeuristic, float] = field(default_factory=dict)
    avg_score: dict[BinPackingHeuristic, float] = field(default_factory=dict)
    last_used: dict[BinPackingHeuristic, float] = field(default_factory=dict)


class DynamicHeuristicSelector:
    _instance: DynamicHeuristicSelector | None = None

    def __new__(cls) -> DynamicHeuristicSelector:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._performance = HeuristicPerformanceRecord()
        return cls._instance

    @classmethod
    def selector(cls) -> DynamicHeuristicSelector:
        return cls()

    def select_heuristic(
        self,
        request: SchedulingRequest,
        available_bins: list[ExecutionCapacity],
    ) -> BinPackingHeuristic:
        features = self._extract_context_features(request, available_bins)

        if request.sla_tier.value == "defense":
            return BinPackingHeuristic.SLA_AWARE_BEST_FIT
        elif features["utilization"] > 0.85:
            return BinPackingHeuristic.BEST_FIT_DECREASING
        elif features["gpu_count_requested"] > 4:
            return BinPackingHeuristic.FIRST_FIT_DECREASING
        elif features["is_realtime"]:
            return BinPackingHeuristic.SLA_AWARE_BEST_FIT
        elif features["available_bins"] <= 2:
            return BinPackingHeuristic.FIRST_FIT_DECREASING
        else:
            return self._choose_by_historical_performance()

    def _extract_context_features(
        self,
        request: SchedulingRequest,
        bins: list[ExecutionCapacity],
    ) -> dict[str, Any]:
        utilization = sum(b.utilization_pct for b in bins) / max(len(bins), 1) / 100
        return {
            "utilization": utilization,
            "gpu_count_requested": request.gpu_count,
            "is_realtime": getattr(request, "realtime", False)
            or getattr(request, "latency_requirement_ms", 9999) < 1000,
            "sla_tier": request.sla_tier.value,
            "requires_itar": getattr(request, "requires_itar", False),
            "available_bins": len(bins),
        }

    def _choose_by_historical_performance(self) -> BinPackingHeuristic:
        if not self._performance.success_rate:
            return BinPackingHeuristic.SLA_AWARE_BEST_FIT

        scores: dict[BinPackingHeuristic, float] = {}
        now = time.time()
        for h in BinPackingHeuristic:
            success = self._performance.success_rate.get(h, 0.5)
            recency_bonus = 0.1 if now - self._performance.last_used.get(h, 0) < 300 else 0.0
            scores[h] = success + recency_bonus

        return max(scores, key=scores.get)

    def record_outcome(
        self,
        heuristic: BinPackingHeuristic,
        success: bool,
        score: float,
    ) -> None:
        prev_success = self._performance.success_rate.get(heuristic, 0.5)
        self._performance.success_rate[heuristic] = prev_success * 0.9 + (1.0 if success else 0.0) * 0.1
        self._performance.avg_score[heuristic] = score
        self._performance.last_used[heuristic] = time.time()

    def get_performance_summary(
        self,
    ) -> dict[BinPackingHeuristic, dict[str, Any]]:
        return {
            h.value: {
                "success_rate": self._performance.success_rate.get(h, 0.0),
                "avg_score": self._performance.avg_score.get(h, 0.0),
                "last_used": self._performance.last_used.get(h, 0.0),
            }
            for h in BinPackingHeuristic
        }


def dynamic_pack(
    request: SchedulingRequest,
    available_bins: list[ExecutionCapacity],
    packer: AdvancedGPUBinPacker,
) -> ExecutionCapacity | None:
    selector = DynamicHeuristicSelector.selector()
    heuristic = selector.select_heuristic(request, available_bins)
    result = packer.pack(request, available_bins, heuristic)
    score = 0.0
    if result:
        score = packer._compute_packing_score(packer._to_bin(result), request).total
    selector.record_outcome(heuristic, result is not None, score)
    return result
