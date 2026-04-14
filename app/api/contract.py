"""
API Contract — Strict boundary between frontend and backend

This is the ONLY public interface to the execution engine.
Frontend MUST only interact through these schemas.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, List, Optional
import time

API_VERSION = "v1"

MAX_DAG_SIZE = 1000
MAX_CONTEXT_SIZE = 10000


class DAGNodeSchema(BaseModel):
    fn: str = Field(..., description="Task function name")
    deps: List[str] = Field(default_factory=list, description="Dependency node names")


class RunRequest(BaseModel):
    dag: Dict[str, DAGNodeSchema] = Field(..., description="DAG definition")
    context: Dict[str, Any] = Field(
        default_factory=dict, description="Execution context"
    )
    mode: str = Field(
        default="local", description="Execution mode: local, subprocess, remote"
    )

    @field_validator("dag")
    @classmethod
    def validate_dag_size(cls, v):
        if len(v) > MAX_DAG_SIZE:
            raise ValueError(f"DAG too large: {len(v)} nodes (max: {MAX_DAG_SIZE})")
        return v

    @field_validator("context")
    @classmethod
    def validate_context_size(cls, v):
        import json

        if len(json.dumps(v)) > MAX_CONTEXT_SIZE:
            raise ValueError(f"Context too large (max: {MAX_CONTEXT_SIZE} bytes)")
        return v

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v):
        if v not in {"local", "subprocess", "remote"}:
            raise ValueError(f"Invalid mode: {v}")
        return v


class RunResponse(BaseModel):
    results: Dict[str, Any] = Field(..., description="Execution results")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")
    status: str = Field(..., description="Execution status: ok, error")
    version: str = Field(default=API_VERSION, description="API version")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    trace: List[Dict[str, Any]] = Field(
        default_factory=list, description="Execution trace"
    )


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: float = Field(default_factory=time.time)


def error_response(message: str) -> RunResponse:
    return RunResponse(results={}, execution_time_ms=0, status="error", error=message)
