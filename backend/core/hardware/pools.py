# backend/core/hardware/pools.py
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class PoolClass(str, Enum):
    SHARED = "shared"
    DEDICATED = "dedicated"
    ISOLATED = "isolated"
    LOW_COST = "low_cost"
    REALTIME = "realtime"
    HIGH_MEMORY = "high_memory"


class ExecutionCapacity(BaseModel):
    id: str
    pool_class: PoolClass
    provider: str
    node_id: str
    gpu_type: str
    gpu_count: int
    vram_gb: int
    status: str = "WARM_IDLE"
    utilization_pct: float = 0.0
    itar_eligible: bool = False
    hourly_cost_usd: float
    supports_mig: bool = False
    metadata: dict = Field(default_factory=dict)
