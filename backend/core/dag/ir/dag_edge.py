from __future__ import annotations

from pydantic import BaseModel

from backend.core.dag.ir.dag_types import EdgeType


class DAGEdge(BaseModel):
    source: str
    target: str
    edge_type: EdgeType = EdgeType.DATAFLOW
    condition: str | None = None
    probability: float | None = None
