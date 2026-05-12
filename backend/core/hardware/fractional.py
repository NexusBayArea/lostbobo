from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from backend.core.hardware.pools import ExecutionCapacity

if TYPE_CHECKING:
    from backend.core.hardware.isolation import GPUIsolationManager
from backend.hardware.scheduler import SchedulingRequest
from backend.core.services.observability_service import observability


@dataclass
class FractionalAllocation:
    allocation_id: str
    capacity_id: str
    gpu_fraction: float
    memory_fraction: float
    priority: int
    tenant_id: str
    expires_at: float
    workload_type: str


class FractionalGPUScheduler:
    """Fractional GPU allocator with isolation enforcement."""

    _instance = None
    _active_allocations: dict[str, list[FractionalAllocation]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def scheduler(cls) -> FractionalGPUScheduler:
        return cls()

    async def allocate(
        self,
        request: SchedulingRequest,
        capacity: ExecutionCapacity,
    ) -> FractionalAllocation | None:
        """Create fractional allocation and enforce isolation."""
        if request.gpu_count >= 1.0:
            return None  # Full GPU - use classic path

        gpu_frac = float(request.gpu_count)
        mem_frac = float(getattr(request, "gpu_memory_required", 8.0)) / (capacity.vram_gb or 40)

        current = self._get_current_usage(capacity.id)
        if current["gpu"] + gpu_frac > 1.05 or current["mem"] + mem_frac > 1.05:
            return None

        allocation = FractionalAllocation(
            allocation_id=str(uuid.uuid4()),
            capacity_id=capacity.id,
            gpu_fraction=gpu_frac,
            memory_fraction=mem_frac,
            priority=getattr(request, "priority", 50),
            tenant_id=request.tenant_id,
            expires_at=datetime.utcnow().timestamp() + getattr(request, "estimated_runtime_seconds", 3600),
            workload_type=getattr(request, "workload_type", "default"),
        )

        # Enforce isolation
        from backend.core.hardware.isolation import GPUIsolationManager

        success = await GPUIsolationManager.manager().apply_isolation(capacity, allocation, request)
        if not success:
            return None

        self._active_allocations.setdefault(capacity.id, []).append(allocation)
        observability().increment("fractional_allocations_total")

        return allocation

    def _get_current_usage(self, capacity_id: str) -> dict[str, float]:
        allocs = self._active_allocations.get(capacity_id, [])
        return {
            "gpu": sum(a.gpu_fraction for a in allocs),
            "mem": sum(a.memory_fraction for a in allocs),
        }

    async def release(self, allocation_id: str):
        """Release a fractional allocation."""
        for cap_id, allocs in list(self._active_allocations.items()):
            self._active_allocations[cap_id] = [a for a in allocs if a.allocation_id != allocation_id]
            if not self._active_allocations[cap_id]:
                del self._active_allocations[cap_id]
                from backend.core.hardware.isolation import GPUIsolationManager

                await GPUIsolationManager.manager().release(allocation_id)


def get_fractional_scheduler() -> FractionalGPUScheduler:
    return FractionalGPUScheduler.scheduler()
