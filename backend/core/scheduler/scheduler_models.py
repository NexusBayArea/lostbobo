from __future__ import annotations

from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class WorkloadPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class SLAClass(str, Enum):
    REALTIME = "realtime"
    INTERACTIVE = "interactive"
    BATCH = "batch"


class WorkloadType(str, Enum):
    DAG = "dag"
    INFERENCE = "inference"
    SIMULATION = "simulation"
    TRAINING = "training"


class SchedulingDecision(str, Enum):
    ACCEPTED = "accepted"
    QUEUED = "queued"
    REJECTED = "rejected"
    PREEMPTED = "preempted"


class ResourceRequest(BaseModel):
    cpu_cores: float = 1.0
    memory_mb: int = 1024
    gpu_fraction: float = 0.0
    gpu_type: str | None = None
    max_runtime_seconds: int = 300


class Workload(BaseModel):
    workload_id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    plugin_name: str
    workload_type: WorkloadType
    priority: WorkloadPriority = WorkloadPriority.NORMAL
    sla_class: SLAClass = SLAClass.BATCH
    resources: ResourceRequest
    dag_id: str | None = None
    dag_node_id: str | None = None
    deterministic_replay: bool = True
    speculative: bool = False
    budget_limit_usd: float | None = None
