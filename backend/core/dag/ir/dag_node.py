from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from backend.core.dag.ir.dag_types import NodeExecutionType, NodeState, RetryPolicy


class ResourceRequirements(BaseModel):
    cpu_cores: float = 1.0
    memory_mb: int = 512
    gpu_fraction: float = 0.0
    gpu_type: str | None = None


class DAGNode(BaseModel):
    node_id: str
    node_type: str
    execution_type: NodeExecutionType = NodeExecutionType.TASK
    capability: str = ""
    plugin_name: str = ""
    inputs: dict[str, Any] = {}
    outputs: list[str] = []
    dependencies: list[str] = []
    resources: ResourceRequirements = ResourceRequirements()
    retry_policy: RetryPolicy = RetryPolicy.SIMPLE
    timeout_seconds: int = 300
    deterministic: bool = True
    speculative: bool = False
    checkpoint_enabled: bool = True
    state: NodeState = NodeState.PENDING
    metadata: dict[str, Any] = {}
