from __future__ import annotations

from pydantic import BaseModel


class ExecutionContract(BaseModel):
    execution_id: str
    dag_id: str
    tenant_id: str
    node_id: str
    capability: str
    payload: dict
