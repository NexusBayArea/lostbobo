"""Re-exported hardware types for the core layer."""

from __future__ import annotations

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
from backend.hardware.scheduler import (
    SchedulingRequest,
    SchedulingResult,
    get_scheduler,
)
from backend.hardware.sla import SLATier

__all__ = [
    "GPUType",
    "IsolationLevel",
    "NodeStatus",
    "ProviderHealth",
    "ProviderInterface",
    "GPUNode",
    "get_provider_registry",
    "CapacityReservation",
    "CapacityReservationSystem",
    "ReservationType",
    "get_reservation_system",
    "SchedulingRequest",
    "SchedulingResult",
    "get_scheduler",
    "SLATier",
    "PlacementEngine",
    "PlacementPolicy",
]
