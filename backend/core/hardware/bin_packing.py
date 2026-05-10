"""Advanced multi-heuristic GPU bin packing for hardware moat optimization."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from backend.core.hardware.pools import ExecutionCapacity, PoolClass
from backend.hardware.scheduler import SchedulingRequest
from backend.hardware.sla import SLATier


class BinPackingHeuristic(str, Enum):
    FIRST_FIT_DECREASING = "first_fit_decreasing"
    BEST_FIT_DECREASING = "best_fit_decreasing"
    WORST_FIT_DECREASING = "worst_fit_decreasing"
    SLA_AWARE_BEST_FIT = "sla_aware_best_fit"


@dataclass
class PackingScore:
    fit_score: float
    sla_compliance: float
    cost_score: float
    fragmentation_penalty: float
    total: float


@dataclass
class GPUBin:
    capacity_id: str
    gpu_type: str
    total_gpus: float
    available_gpus: float
    vram_gb: int
    current_workloads: list[dict[str, Any]] = field(default_factory=list)
    isolation_level: str
    itar_eligible: bool
    hourly_cost_usd: float
    metadata: dict[str, Any] = field(default_factory=dict)


class AdvancedGPUBinPacker:
    def pack(
        self,
        request: SchedulingRequest,
        available_bins: list[ExecutionCapacity],
        heuristic: BinPackingHeuristic = BinPackingHeuristic.SLA_AWARE_BEST_FIT,
    ) -> ExecutionCapacity | None:
        bins = [self._to_bin(cap) for cap in available_bins if self._can_fit(cap, request)]

        if not bins:
            return None

        match heuristic:
            case BinPackingHeuristic.FIRST_FIT_DECREASING:
                return self._first_fit_decreasing(bins, request)
            case BinPackingHeuristic.BEST_FIT_DECREASING:
                return self._best_fit_decreasing(bins, request)
            case BinPackingHeuristic.WORST_FIT_DECREASING:
                return self._worst_fit_decreasing(bins, request)
            case BinPackingHeuristic.SLA_AWARE_BEST_FIT:
                return self._sla_aware_best_fit(bins, request)

    def _sla_aware_best_fit(
        self,
        bins: list[GPUBin],
        request: SchedulingRequest,
    ) -> ExecutionCapacity | None:
        best_score = float("inf")
        best_bin: GPUBin | None = None

        for bin in bins:
            score = self._compute_packing_score(bin, request)
            if score.total < best_score:
                best_score = score.total
                best_bin = bin

        if best_bin:
            return self._assign(best_bin, request)
        return None

    def _compute_packing_score(self, bin: GPUBin, request: SchedulingRequest) -> PackingScore:
        remaining_gpus = bin.available_gpus - request.gpu_count
        fit_score = remaining_gpus / bin.total_gpus if remaining_gpus >= 0 else 9999

        sla_score = 1.0
        if request.sla_tier == SLATier.DEFENSE and bin.isolation_level != "isolated":
            sla_score = 0.0
        elif request.sla_tier == SLATier.ENTERPRISE and bin.isolation_level not in ("dedicated", "isolated"):
            sla_score = 0.5

        cost_score = bin.hourly_cost_usd / request.gpu_count

        frag_penalty = max(0.0, (remaining_gpus / bin.total_gpus) ** 2) if remaining_gpus > 0 else 0.0

        total_score = fit_score * 0.4 + (1.0 - sla_score) * 0.3 + cost_score * 0.2 + frag_penalty * 0.1

        return PackingScore(
            fit_score=fit_score,
            sla_compliance=sla_score,
            cost_score=cost_score,
            fragmentation_penalty=frag_penalty,
            total=total_score,
        )

    def _first_fit_decreasing(
        self,
        bins: list[GPUBin],
        request: SchedulingRequest,
    ) -> ExecutionCapacity | None:
        sorted_bins = sorted(bins, key=lambda b: -b.available_gpus)
        for bin in sorted_bins:
            if bin.available_gpus >= request.gpu_count:
                return self._assign(bin, request)
        return None

    def _best_fit_decreasing(
        self,
        bins: list[GPUBin],
        request: SchedulingRequest,
    ) -> ExecutionCapacity | None:
        sorted_bins = sorted(bins, key=lambda b: -b.available_gpus)
        best: GPUBin | None = None
        best_remaining = float("inf")

        for bin in sorted_bins:
            remaining = bin.available_gpus - request.gpu_count
            if remaining >= 0 and remaining < best_remaining:
                best_remaining = remaining
                best = bin

        if best:
            return self._assign(best, request)
        return None

    def _worst_fit_decreasing(
        self,
        bins: list[GPUBin],
        request: SchedulingRequest,
    ) -> ExecutionCapacity | None:
        sorted_bins = sorted(bins, key=lambda b: -b.available_gpus)
        best: GPUBin | None = None
        best_remaining = -float("inf")

        for bin in sorted_bins:
            remaining = bin.available_gpus - request.gpu_count
            if remaining >= 0 and remaining > best_remaining:
                best_remaining = remaining
                best = bin

        if best:
            return self._assign(best, request)
        return None

    def _to_bin(self, capacity: ExecutionCapacity) -> GPUBin:
        used = sum(w.get("gpu_fraction", 0.0) for w in capacity.metadata.get("workloads", []))
        available = max(0.0, float(capacity.gpu_count) - used)
        return GPUBin(
            capacity_id=capacity.id,
            gpu_type=capacity.gpu_type,
            total_gpus=float(capacity.gpu_count),
            available_gpus=available,
            vram_gb=capacity.metadata.get("vram_gb", 48),
            current_workloads=capacity.metadata.get("workloads", []),
            isolation_level=capacity.pool_class.value,
            itar_eligible=capacity.itar_eligible,
            hourly_cost_usd=capacity.hourly_cost_usd,
            metadata=capacity.metadata,
        )

    def _can_fit(self, capacity: ExecutionCapacity, request: SchedulingRequest) -> bool:
        used = sum(w.get("gpu_fraction", 0.0) for w in capacity.metadata.get("workloads", []))
        available = max(0.0, float(capacity.gpu_count) - used)
        if request.data_classification == "ITAR" and not capacity.itar_eligible:
            return False
        if request.gpu_count > available:
            return False
        required_isolation = {
            "defense": "isolated",
            "enterprise": "dedicated",
        }.get(request.sla_tier.value, "shared")
        if required_isolation != "shared" and capacity.pool_class.value != required_isolation:
            return False
        return True

    def _assign(self, bin: GPUBin, request: SchedulingRequest) -> ExecutionCapacity:
        workloads = list(bin.current_workloads)
        workloads.append(
            {
                "run_id": request.run_id,
                "gpu_count": request.gpu_count,
                "gpu_fraction": request.gpu_count / bin.total_gpus,
            }
        )
        new_utilization = min(
            100.0, (1 - bin.available_gpus / bin.total_gpus + request.gpu_count / bin.total_gpus) * 100
        )
        return ExecutionCapacity(
            id=bin.capacity_id,
            pool_class=PoolClass(bin.isolation_level),
            provider=bin.metadata.get("provider", "unknown"),
            node_id=bin.metadata.get("node_id", ""),
            gpu_type=bin.gpu_type,
            gpu_count=request.gpu_count,
            status="RUNNING",
            itar_eligible=bin.itar_eligible,
            utilization_pct=new_utilization,
            hourly_cost_usd=bin.hourly_cost_usd,
            warm_since=bin.metadata.get("warm_since", ""),
            metadata={"workloads": workloads},
        )

    def calculate_utilization(
        self,
        bins: list[ExecutionCapacity],
    ) -> dict[str, Any]:
        total_gpus = sum(b.gpu_count for b in bins)
        total_used = sum(b.gpu_count * b.utilization_pct / 100 for b in bins)
        return {
            "total_bins": len(bins),
            "total_gpus": total_gpus,
            "total_used": round(total_used, 2),
            "utilization_pct": round((total_used / total_gpus * 100) if total_gpus else 0, 2),
            "wasted_bins": sum(1 for b in bins if b.utilization_pct < 50),
            "optimized_bins": sum(1 for b in bins if b.utilization_pct >= 70),
        }


_packer: AdvancedGPUBinPacker | None = None


def get_advanced_gpu_bin_packer() -> AdvancedGPUBinPacker:
    global _packer
    if _packer is None:
        _packer = AdvancedGPUBinPacker()
    return _packer
