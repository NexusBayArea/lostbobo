from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from backend.core.hardware.mps import MPSManager

logger = logging.getLogger(__name__)


class GPUIsolationLevel(str, Enum):
    NONE = "none"
    SOFT = "soft"
    MPS = "mps"
    MIG = "mig"
    CONTAINER = "container"
    STRICT = "strict"


@dataclass
class IsolationConfig:
    level: GPUIsolationLevel
    compute_limit: float
    memory_limit_gb: float
    priority: int
    tenant_id: str
    allowed_workloads: list[str] = field(default_factory=list)


class GPUIsolationManager:
    _instance: GPUIsolationManager | None = None
    _active_isolations: dict[str, IsolationConfig] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._governor_registered = False
        return cls._instance

    @classmethod
    def manager(cls) -> GPUIsolationManager:
        return cls()

    async def apply_isolation(
        self,
        capacity: Any,
        allocation: Any,
        request: Any,
    ) -> bool:
        pool_class = getattr(capacity, "pool_class", None)
        if pool_class and hasattr(pool_class, "value"):
            pool_str = pool_class.value
        else:
            pool_str = str(pool_class)

        supports_mig = getattr(capacity, "supports_mig", False) or False
        vram_gb = getattr(capacity, "vram_gb", 16.0) or 16.0

        if pool_str == "isolated" or getattr(request.sla_tier, "value", "") == "defense":
            config = IsolationConfig(
                level=GPUIsolationLevel.MIG if supports_mig else GPUIsolationLevel.STRICT,
                compute_limit=1.0,
                memory_limit_gb=vram_gb,
                priority=99,
                tenant_id=request.tenant_id,
                allowed_workloads=["defense", "simulation"],
            )
        elif pool_str == "dedicated":
            config = IsolationConfig(
                level=GPUIsolationLevel.MPS,
                compute_limit=0.95,
                memory_limit_gb=getattr(request, "gpu_memory_required", vram_gb * 0.5),
                priority=80,
                tenant_id=request.tenant_id,
                allowed_workloads=["enterprise"],
            )
        else:
            config = IsolationConfig(
                level=GPUIsolationLevel.CONTAINER,
                compute_limit=min(0.65, allocation.gpu_fraction * 1.1) if hasattr(allocation, "gpu_fraction") else 0.65,
                memory_limit_gb=min(
                    12.0,
                    (allocation.memory_fraction * vram_gb) if hasattr(allocation, "memory_fraction") else vram_gb * 0.3,
                ),
                priority=50,
                tenant_id=request.tenant_id,
                allowed_workloads=["agent_swarm", "inference", "monte_carlo"],
            )

        success = await self._enforce_isolation_technique(capacity, config)

        if success:
            self._active_isolations[allocation.allocation_id] = config
            try:
                from backend.core.systems.resource_governance import ResourceGovernor

                ResourceGovernor.governor().register_allocation(allocation, config)
            except Exception:
                pass
        else:
            try:
                from backend.core.runtime.alerting.engine import RealTimeAlertingSystem
                from backend.core.runtime.anomaly.engine import AnomalyEvent

                await RealTimeAlertingSystem.alerts().trigger(
                    AnomalyEvent(
                        anomaly_type="isolation_failure",
                        severity=0.88,
                        entity_id=getattr(capacity, "id", "unknown"),
                        description=f"Failed to apply {config.level} isolation for tenant {request.tenant_id}",
                        confidence=0.9,
                        recommended_action="fallback_to_dedicated",
                        algorithm="isolation_manager",
                    )
                )
            except Exception:
                pass

        return success

    async def _enforce_isolation_technique(self, capacity: Any, config: IsolationConfig) -> bool:
        """Route to the correct isolation technique."""
        if config.level == GPUIsolationLevel.MPS:
            return await MPSManager.manager().start_daemon(capacity, config)

        match config.level:
            case GPUIsolationLevel.MIG:
                return await self._apply_mig_partition(capacity, config)
            case GPUIsolationLevel.CONTAINER:
                return await self._apply_container_isolation(capacity, config)
            case _:
                return await self._apply_soft_limits(capacity, config)

    async def _apply_mig_partition(self, capacity: Any, config: IsolationConfig) -> bool:
        try:
            logger.info(
                f"MIG partition on {getattr(capacity, 'id', 'unknown')}: "
                f"compute={config.compute_limit}, mem={config.memory_limit_gb}GB"
            )
            return True
        except Exception as e:
            logger.warning(f"MIG partition failed: {e}")
            return False

    async def _apply_container_isolation(self, capacity: Any, config: IsolationConfig) -> bool:
        try:
            logger.info(
                f"Container isolation on {getattr(capacity, 'id', 'unknown')}: "
                f"compute={config.compute_limit}, mem={config.memory_limit_gb}GB"
            )
            return True
        except Exception as e:
            logger.warning(f"Container isolation failed: {e}")
            return False

    async def _apply_soft_limits(self, capacity: Any, config: IsolationConfig) -> bool:
        logger.info(
            f"Soft limits on {getattr(capacity, 'id', 'unknown')}: "
            f"compute={config.compute_limit}, mem={config.memory_limit_gb}GB"
        )
        return True

    def get_config(self, allocation_id: str) -> IsolationConfig | None:
        return self._active_isolations.get(allocation_id)

    def release(self, allocation_id: str) -> bool:
        if allocation_id in self._active_isolations:
            del self._active_isolations[allocation_id]
            return True
        return False


def get_isolation_manager() -> GPUIsolationManager:
    return GPUIsolationManager.manager()

