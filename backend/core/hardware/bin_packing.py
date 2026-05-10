"""Intelligent GPU bin packing for hardware moat optimization."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.core.hardware.pools import ExecutionCapacity, PoolClass
from backend.hardware.scheduler import SchedulingRequest


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

    def fractional_available(self) -> float:
        used = sum(w.get("gpu_fraction", 0.0) for w in self.current_workloads)
        return max(0.0, self.total_gpus - used)


class GPUBinPacker:
    def pack(
        self,
        request: SchedulingRequest,
        available_bins: list[ExecutionCapacity],
    ) -> ExecutionCapacity | None:
        bins = [self._to_bin(cap) for cap in available_bins]
        sorted_bins = sorted(
            bins,
            key=lambda b: (
                0 if self._meets_isolation(b, request) else 1,
                -b.fractional_available() if request.gpu_count > 1 else 0,
                0 if not b.current_workloads else 1,
                b.hourly_cost_usd,
            ),
        )
        for bin in sorted_bins:
            if self._can_fit(bin, request):
                return self._assign_to_bin(bin, request)
        return None

    def pack_fractional(
        self,
        request: SchedulingRequest,
        available_bins: list[ExecutionCapacity],
        gpu_fraction: float = 1.0,
    ) -> tuple[ExecutionCapacity | None, float]:
        bins = [self._to_bin(cap) for cap in available_bins]
        for bin in bins:
            if self._can_fit_fractional(bin, request, gpu_fraction):
                return self._assign_fractional(bin, request, gpu_fraction), gpu_fraction
        return None, 0.0

    def _to_bin(self, capacity: ExecutionCapacity) -> GPUBin:
        return GPUBin(
            capacity_id=capacity.id,
            gpu_type=capacity.gpu_type,
            total_gpus=float(capacity.gpu_count),
            available_gpus=float(capacity.gpu_count) * (1 - capacity.utilization_pct / 100),
            vram_gb=capacity.metadata.get("vram_gb", 48),
            current_workloads=capacity.metadata.get("workloads", []),
            isolation_level=capacity.pool_class.value,
            itar_eligible=capacity.itar_eligible,
            hourly_cost_usd=capacity.hourly_cost_usd,
            metadata=capacity.metadata,
        )

    def _can_fit(self, bin: GPUBin, request: SchedulingRequest) -> bool:
        if request.data_classification == "ITAR" and not bin.itar_eligible:
            return False
        if request.gpu_count > bin.fractional_available():
            return False
        required_isolation = {
            "defense": "isolated",
            "enterprise": "dedicated",
        }.get(request.sla_tier.value, "shared")
        if required_isolation != "shared" and bin.isolation_level != required_isolation:
            return False
        return True

    def _can_fit_fractional(self, bin: GPUBin, request: SchedulingRequest, fraction: float) -> bool:
        required_gpus = request.gpu_count * fraction
        if request.data_classification == "ITAR" and not bin.itar_eligible:
            return False
        if required_gpus > bin.fractional_available():
            return False
        required_isolation = {
            "defense": "isolated",
            "enterprise": "dedicated",
        }.get(request.sla_tier.value, "shared")
        if required_isolation != "shared" and bin.isolation_level != required_isolation:
            return False
        return True

    def _assign_to_bin(self, bin: GPUBin, request: SchedulingRequest) -> ExecutionCapacity:
        return ExecutionCapacity(
            id=bin.capacity_id,
            pool_class=PoolClass(bin.isolation_level),
            provider=bin.metadata.get("provider", "unknown"),
            node_id=bin.metadata.get("node_id", ""),
            gpu_type=bin.gpu_type,
            gpu_count=request.gpu_count,
            status="RUNNING",
            itar_eligible=bin.itar_eligible,
            utilization_pct=min(100.0, bin.available_gpus / bin.total_gpus * 100),
            hourly_cost_usd=bin.hourly_cost_usd,
            warm_since=bin.metadata.get("warm_since", ""),
        )

    def _assign_fractional(
        self,
        bin: GPUBin,
        request: SchedulingRequest,
        fraction: float,
    ) -> ExecutionCapacity:
        workloads = list(bin.current_workloads)
        workloads.append(
            {
                "run_id": request.run_id,
                "gpu_fraction": fraction,
                "gpu_count": request.gpu_count,
            }
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
            utilization_pct=min(
                100.0, (1 - bin.fractional_available() / bin.total_gpus + fraction / bin.total_gpus) * 100
            ),
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


_packer: GPUBinPacker | None = None


def get_gpu_bin_packer() -> GPUBinPacker:
    global _packer
    if _packer is None:
        _packer = GPUBinPacker()
    return _packer
