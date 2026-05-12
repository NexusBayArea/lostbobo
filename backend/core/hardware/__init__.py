"""Re-exported hardware types for the core layer."""

from __future__ import annotations

from backend.core.hardware.economics import (
    CostModel,
    EconomicScore,
    NodeEconomics,
    ResourceEconomicsRuntime,
    get_economics_engine,
)
from backend.core.hardware.fractional import FractionalAllocation, FractionalGPUScheduler, get_fractional_scheduler
from backend.core.hardware.isolation import (
    GPUIsolationConfig,
    GPUIsolationLevel,
    GPUIsolationManager,
    get_isolation_manager,
)
from backend.core.hardware.placement import PlacementEngine, PlacementPolicy
from backend.hardware.providers import (
    GPUNode,
    GPUType,
    IsolationLevel,
    NodeStatus,
    ProviderHealth,
    ProviderInterface,
    get_provider_registry,
)
from backend.hardware.reservations import (
    CapacityReservation,
    CapacityReservationSystem,
    ReservationType,
    get_reservation_system,
)
from backend.hardware.scheduler import SchedulingRequest, get_scheduler
from backend.hardware.sla import SLATier

__all__ = [
    "CostModel",
    "EconomicScore",
    "FractionalAllocation",
    "FractionalGPUScheduler",
    "GPUIsolationConfig",
    "GPUIsolationLevel",
    "GPUIsolationManager",
    "GPUType",
    "IsolationLevel",
    "NodeEconomics",
    "NodeStatus",
    "PlacementEngine",
    "PlacementPolicy",
    "ProviderHealth",
    "ProviderInterface",
    "GPUNode",
    "get_provider_registry",
    "CapacityReservation",
    "CapacityReservationSystem",
    "ReservationType",
    "get_reservation_system",
    "SchedulingRequest",
    "get_scheduler",
    "SLATier",
    "ResourceEconomicsRuntime",
    "get_economics_engine",
    "get_fractional_scheduler",
    "get_isolation_manager",
]
