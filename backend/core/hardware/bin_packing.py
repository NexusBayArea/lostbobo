# backend/core/hardware/bin_packing.py
from __future__ import annotations

from dataclasses import dataclass

from backend.core.hardware.fractional import FractionalGPUScheduler
from backend.core.hardware.pools import ExecutionCapacity, PoolClass
from backend.hardware.scheduler import SchedulingRequest
from backend.core.services.observability_service import observability
from backend.core.tracing import trace_context


@dataclass
class PackingScore:
    total: float
    fit_score: float
    sla_score: float


class AdvancedGPUBinPacker:
    """Advanced bin packer with fractional GPU support."""

    async def pack(
        self,
        request: SchedulingRequest,
        available_bins: list[ExecutionCapacity],
    ) -> ExecutionCapacity | None:
        with trace_context("bin_packing.pack") as span:
            observability().increment("bin_packing_attempts_total")

            # 1. Try fractional allocation first for small requests
            if request.gpu_count < 1.0:
                for bin_cap in available_bins:
                    alloc = await FractionalGPUScheduler.scheduler().allocate(request, bin_cap)
                    if alloc:
                        observability().increment("fractional_packing_success")
                        span.set_attribute("packing_type", "fractional")
                        return bin_cap

            # 2. Full GPU bin packing (existing logic)
            sorted_bins = sorted(
                available_bins,
                key=lambda b: (
                    0 if b.pool_class == PoolClass.ISOLATED and request.sla_tier == "defense" else 1,
                    -b.utilization_pct,  # prefer less loaded
                ),
            )

            for bin_cap in sorted_bins:
                if self._can_fit(bin_cap, request):
                    span.set_attribute("packing_type", "full")
                    return bin_cap

            return None

    def _can_fit(self, capacity: ExecutionCapacity, request: SchedulingRequest) -> bool:
        if request.gpu_count > (capacity.gpu_count * (1.0 - capacity.utilization_pct / 100)):
            return False
        if getattr(request, "requires_itar", False) and not capacity.itar_eligible:
            return False
        return True
