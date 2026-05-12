from __future__ import annotations

from pydantic import BaseModel


class SchedulerDispatchContract(BaseModel):
    """
    FROZEN scheduling request v1.0.0.
    """

    execution_id: str
    dag_id: str
    priority: int
    tenant_id: str
    gpu_required: bool = False
    estimated_runtime_seconds: float
