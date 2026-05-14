from __future__ import annotations

import hashlib
import json
import uuid
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PortType(str, Enum):
    DATA = "data"
    EVENT = "event"
    STATE = "state"
    CONTROL = "control"


class DAGNodeInput(BaseModel):
    name: str
    type: str
    required: bool = True
    description: str = ""
    default: Any = None
    json_schema: dict[str, Any] = Field(default_factory=dict)


class DAGNodeOutput(BaseModel):
    name: str
    type: str
    description: str = ""
    json_schema: dict[str, Any] = Field(default_factory=dict)


class DAGNodeContract(BaseModel):
    model_config = {"protected_namespaces": ()}
    node_type: str
    version: str = "1.0.0"
    inputs: list[DAGNodeInput] = Field(default_factory=list)
    outputs: list[DAGNodeOutput] = Field(default_factory=list)
    deterministic: bool = True
    idempotent: bool = True
    max_retries: int = 0
    timeout_seconds: int = 300
    required_capabilities: list[str] = Field(default_factory=list)


class DAGEdge(BaseModel):
    source: str
    target: str
    data_mapping: dict[str, str] = Field(default_factory=dict)


class DAGExecutionPlan(BaseModel):
    nodes: list[DAGNodeContract] = Field(default_factory=list)
    edges: list[DAGEdge] = Field(default_factory=list)
    max_concurrency: int = 1
    timeout_seconds: int = 3600


class DAGPort(BaseModel):
    name: str
    port_type: PortType = PortType.DATA
    json_schema: dict[str, Any] | None = None
    required: bool = True
    default: Any = None


class DAGNode(BaseModel):
    node_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    node_type: str
    plugin_name: str | None = None
    inputs: dict[str, Any] = Field(default_factory=dict)
    outputs: dict[str, DAGPort] = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    priority: int = 0
    timeout_seconds: int = 3600
    retry_policy: dict[str, Any] | None = None


class DAGEdgeDetail(BaseModel):
    edge_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    source_node_id: str
    source_port: str
    target_node_id: str
    target_port: str
    condition: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DAGGraph(BaseModel):
    dag_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    name: str = ""
    version: str = "1.0.0"
    nodes: list[DAGNode] = Field(default_factory=list)
    edges: list[DAGEdgeDetail] = Field(default_factory=list)
    created_by: str = ""
    tenant_id: str = "default"
    tags: dict[str, str] = Field(default_factory=dict)
    created_at: str | None = None
    scheduling_policy: str = "topological"
    max_parallelism: int = 10
    deadline_seconds: int | None = None
    parent_dag_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(self.model_dump(mode="json"), sort_keys=True)

    def hash(self) -> str:
        return hashlib.sha256(self.to_json().encode()).hexdigest()

    @classmethod
    def from_json(cls, data: str) -> DAGGraph:
        return cls.model_validate_json(data)

    def validate_nodes_exist(self, registered_nodes: set[str]) -> list[str]:
        missing = []
        for node in self.nodes:
            if node.node_type not in registered_nodes:
                missing.append(node.node_type)
        return missing

    def topological_order(self) -> list[str]:
        in_degree: dict[str, int] = {n.node_id: 0 for n in self.nodes}
        adj: dict[str, list[str]] = {n.node_id: [] for n in self.nodes}
        for node in self.nodes:
            for dep in node.depends_on:
                adj[dep].append(node.node_id)
                in_degree[node.node_id] += 1
        for edge in self.edges:
            adj.setdefault(edge.source_node_id, [])
            adj[edge.source_node_id].append(edge.target_node_id)
            in_degree[edge.target_node_id] = in_degree.get(edge.target_node_id, 0) + 1
        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        order = []
        while queue:
            nid = queue.pop(0)
            order.append(nid)
            for neighbor in adj.get(nid, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        if len(order) != len(self.nodes):
            raise ValueError("DAG has cycles")
        return order
