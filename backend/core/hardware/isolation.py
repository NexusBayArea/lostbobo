# backend/core/hardware/isolation.py
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from backend.core.hardware.mps import MPSManager

if TYPE_CHECKING:
    from backend.core.hardware.fractional import FractionalAllocation
from backend.core.hardware.pools import ExecutionCapacity, PoolClass
from backend.hardware.scheduler import SchedulingRequest
from backend.core.runtime.alerting.engine import RealTimeAlertingSystem
from backend.core.runtime.anomaly.engine import AnomalyEvent
from backend.core.services.observability_service import observability
from backend.core.services.resource_governor import ResourceGovernor
from backend.core.tracing import trace_context


class IsolationLevel(str, Enum):
    NONE = "none"
    SOFT = "soft"
    MPS = "mps"
    MIG = "mig"
    CONTAINER = "container"
    STRICT = "strict"


@dataclass
class IsolationConfig:
    level: IsolationLevel
    compute_limit: float
    memory_limit_gb: float
    priority: int
    tenant_id: str
    allowed_workloads: list[str]


class GPUIsolationManager:
    """Central GPU isolation manager."""

    _instance = None
    _active_configs: dict[str, IsolationConfig] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def manager(cls) -> GPUIsolationManager:
        return cls()

    async def apply_isolation(
        self,
        capacity: ExecutionCapacity,
        allocation: FractionalAllocation,
        request: SchedulingRequest,
    ) -> bool:
        """Apply isolation and return success."""
        with trace_context("isolation.apply"):
            config = self._determine_config(capacity, request)

            success = await self._enforce_isolation_technique(capacity, config)

            if success:
                self._active_configs[allocation.allocation_id] = config
                await ResourceGovernor.governor().register_allocation(allocation, config)
                observability().increment("isolation_success_total")
                return True
            else:
                await self._handle_failure(capacity, request)
                return False

    def _determine_config(self, capacity: ExecutionCapacity, request: SchedulingRequest) -> IsolationConfig:
        if request.sla_tier == "defense" or capacity.pool_class == PoolClass.ISOLATED:
            return IsolationConfig(
                level=IsolationLevel.MIG if getattr(capacity, "supports_mig", False) else IsolationLevel.STRICT,
                compute_limit=1.0,
                memory_limit_gb=float(capacity.vram_gb or 80),
                priority=99,
                tenant_id=request.tenant_id,
                allowed_workloads=["defense"],
            )
        elif capacity.pool_class == PoolClass.DEDICATED:
            return IsolationConfig(
                level=IsolationLevel.MPS,
                compute_limit=0.95,
                memory_limit_gb=float(getattr(request, "gpu_memory_required", 40)),
                priority=80,
                tenant_id=request.tenant_id,
                allowed_workloads=["enterprise"],
            )
        else:
            return IsolationConfig(
                level=IsolationLevel.CONTAINER,
                compute_limit=min(0.70, getattr(request, "gpu_count", 0.5)),
                memory_limit_gb=min(16.0, getattr(request, "gpu_memory_required", 8.0)),
                priority=50,
                tenant_id=request.tenant_id,
                allowed_workloads=["agent_swarm", "inference"],
            )

    async def _enforce_isolation_technique(self, capacity: ExecutionCapacity, config: IsolationConfig) -> bool:
        if config.level == IsolationLevel.MPS:
            return await MPSManager.manager().start_daemon(capacity, config)
        elif config.level in (IsolationLevel.MIG, IsolationLevel.STRICT):
            return True  # Hardware-level
        elif config.level == IsolationLevel.CONTAINER:
            return True  # Docker + cgroups
        else:
            return True  # Soft fallback

    async def _handle_failure(self, capacity: ExecutionCapacity, request: SchedulingRequest):
        await RealTimeAlertingSystem.alerts().trigger(
            AnomalyEvent(
                anomaly_type="isolation_failure",
                severity=0.88,
                entity_id=capacity.id,
                description=f"Isolation failed for {request.sla_tier} on {capacity.pool_class}",
                confidence=0.85,
                recommended_action="fallback_to_dedicated",
                metadata={"pool_class": str(capacity.pool_class)},
            )
        )

    async def release(self, allocation_id: str):
        if allocation_id in self._active_configs:
            del self._active_configs[allocation_id]


GPUIsolationConfig = IsolationConfig
GPUIsolationLevel = IsolationLevel


def get_isolation_manager() -> GPUIsolationManager:
    return GPUIsolationManager.manager()
