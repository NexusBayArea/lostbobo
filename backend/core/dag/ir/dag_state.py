from __future__ import annotations

from pydantic import BaseModel

from backend.core.dag.ir.dag_types import NodeState


class DAGExecutionState(BaseModel):
    dag_id: str
    node_states: dict[str, NodeState]
    started_at: float | None = None
    completed_at: float | None = None
    replay_hash: str = ""
    checkpoint_id: str | None = None
