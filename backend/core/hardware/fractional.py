"""Fractional GPU scheduling for multi-tenant GPU sharing."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


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
    gpu_count: float


class FractionalGPUScheduler:
    _instance: FractionalGPUScheduler | None = None
    _active_allocations: dict[str, list[FractionalAllocation]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def scheduler(cls) -> FractionalGPUScheduler:
        return cls()

    def _is_fractional(self, request: Any) -> bool:
        return request.gpu_count < 1.0

    def _get_current_usage(self, capacity_id: str) -> dict[str, float]:
        allocs = self._active_allocations.get(capacity_id, [])
        now = datetime.now(UTC).timestamp()
        active = [a for a in allocs if a.expires_at > now]
        self._active_allocations[capacity_id] = active
        return {
            "gpu": sum(a.gpu_fraction for a in active),
            "mem": sum(a.memory_fraction for a in active),
        }

    def _can_allocate(self, capacity_id: str, gpu_frac: float, mem_frac: float) -> bool:
        usage = self._get_current_usage(capacity_id)
        return usage["gpu"] + gpu_frac <= 1.05 and usage["mem"] + mem_frac <= 1.05

    async def allocate(
        self,
        request: Any,
        capacity: Any,
    ) -> FractionalAllocation | None:
        if not self._is_fractional(request):
            return None

        if request.sla_tier.value == "defense":
            return None

        gpu_frac = request.gpu_count
        mem_frac = getattr(capacity, "vram_gb", 0) and request.gpu_memory_required / capacity.vram_gb or 0.3

        if not self._can_allocate(capacity.id, gpu_frac, mem_frac):
            return None

        allocation = FractionalAllocation(
            allocation_id=str(uuid.uuid4()),
            capacity_id=capacity.id,
            gpu_fraction=gpu_frac,
            memory_fraction=mem_frac,
            priority=request.priority or 50,
            tenant_id=request.tenant_id,
            expires_at=(getattr(request, "estimated_runtime_seconds", 1800.0) + datetime.now(UTC).timestamp()),
            workload_type=getattr(request, "workload_type", "default"),
            gpu_count=gpu_frac,
        )

        self._active_allocations.setdefault(capacity.id, []).append(allocation)

        try:
            from backend.core.hardware.isolation import get_isolation_manager

            im = get_isolation_manager()
            success = await im.apply_isolation(capacity, allocation, request)
            if not success:
                self._active_allocations[capacity.id] = [
                    a for a in self._active_allocations[capacity.id] if a.allocation_id != allocation.allocation_id
                ]
                return None
        except Exception as e:
            logger.warning(f"Isolation check skipped: {e}")

        try:
            from backend.core.services.observability_service import observability

            obs = observability()
            usage = self._get_current_usage(capacity.id)
            obs.gauge("fractional_gpu_utilization", usage["gpu"], {"capacity_id": capacity.id})
            obs.gauge(
                "shared_gpu_jobs_active",
                len(self._active_allocations.get(capacity.id, [])),
                {"capacity_id": capacity.id},
            )
        except Exception:
            pass

        return allocation

    async def release(self, allocation_id: str) -> bool:
        for cap_id, allocs in list(self._active_allocations.items()):
            remaining = [a for a in allocs if a.allocation_id != allocation_id]
            if len(remaining) < len(allocs):
                self._active_allocations[cap_id] = remaining
                return True
        return False

    def get_active_allocations(self, capacity_id: str) -> list[FractionalAllocation]:
        return list(self._active_allocations.get(capacity_id, []))

    def get_fragmentation(self) -> float:
        total_gpu = sum(self._get_current_usage(c)["gpu"] for c in self._active_allocations)
        total_slots = len(self._active_allocations)
        if total_slots == 0:
            return 0.0
        return max(0.0, 1.0 - (total_gpu / total_slots))

    def record_fractional_usage(self, allocation: FractionalAllocation) -> None:
        try:
            from backend.core.runtime.anomaly.engine import AnomalyDetectionSystem

            AnomalyDetectionSystem.detector().record_scheduling_request(
                {
                    "sla_tier": "professional",
                    "gpu_fraction": allocation.gpu_fraction,
                    "workload_type": allocation.workload_type,
                }
            )
        except Exception:
            pass


def get_fractional_scheduler() -> FractionalGPUScheduler:
    return FractionalGPUScheduler.scheduler()
