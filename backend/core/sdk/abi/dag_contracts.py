from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


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
