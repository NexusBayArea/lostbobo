"""
Execution Trace — Immutable record of every node execution

Provides observability: full replay capability, failure debugging, performance profiling.
Every node execution produces: INPUTS → EXECUTION → OUTPUTS → METADATA
"""

from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List
import time
import uuid


@dataclass
class TraceEvent:
    trace_id: str
    node: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    start_ms: float
    end_ms: float
    duration_ms: float
    status: str  # success, failed
    error: str = None


class TraceBuffer:
    def __init__(self):
        self.events: List[TraceEvent] = []

    def record(self, event: TraceEvent) -> None:
        self.events.append(event)

    def dump(self) -> List[dict]:
        return [asdict(e) for e in self.events]

    def get_node_trace(self, node: str) -> TraceEvent:
        for event in self.events:
            if event.node == node:
                return event
        return None

    def failed_nodes(self) -> List[str]:
        return [e.node for e in self.events if e.status == "failed"]

    def total_duration_ms(self) -> float:
        return sum(e.duration_ms for e in self.events)
