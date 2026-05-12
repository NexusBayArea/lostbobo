from __future__ import annotations

from pydantic import BaseModel


class ExecutionContract(BaseModel):
    """
    FROZEN execution payload contract v1.0.0.
    Payload received by the kernel when invoking a capability.
    """

    execution_id: str
    dag_id: str
    tenant_id: str
    node_id: str
    capability: str
    payload: dict
