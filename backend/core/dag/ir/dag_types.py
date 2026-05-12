from __future__ import annotations

from enum import Enum


class NodeExecutionType(str, Enum):
    TASK = "task"
    INFERENCE = "inference"
    SIMULATION = "simulation"
    AGENT = "agent"
    MAP = "map"
    REDUCE = "reduce"
    ROUTER = "router"
    CONDITION = "condition"
    AGGREGATE = "aggregate"


class NodeState(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


class EdgeType(str, Enum):
    DATAFLOW = "dataflow"
    CONTROLFLOW = "controlflow"
    CONDITIONAL = "conditional"
    PROBABILISTIC = "probabilistic"


class RetryPolicy(str, Enum):
    NEVER = "never"
    SIMPLE = "simple"
    EXPONENTIAL = "exponential"
