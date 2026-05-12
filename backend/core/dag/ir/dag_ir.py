from __future__ import annotations

from uuid import uuid4

from pydantic import BaseModel, Field

from backend.core.dag.ir.dag_edge import DAGEdge
from backend.core.dag.ir.dag_node import DAGNode
from backend.core.dag.ir.replay_metadata import ReplayMetadata


class DAGIR(BaseModel):
    dag_id: str = Field(default_factory=lambda: uuid4().hex)
    name: str = "unnamed"
    version: str = "1.0"
    tenant_id: str = ""
    nodes: list[DAGNode] = Field(default_factory=list)
    edges: list[DAGEdge] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    replay: ReplayMetadata = Field(default_factory=lambda: ReplayMetadata(replay_hash=""))
