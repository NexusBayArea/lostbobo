import json
import time
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


@dataclass
class NodeTrace:
    name: str
    input: Dict[str, Any]
    output: Dict[str, Any]
    status: str
    duration_ms: float


@dataclass
class ExecutionTrace:
    contract_version: str
    timestamp: float
    nodes: List[NodeTrace]
    manifest_hash: Optional[str] = None

    def save(self, path: str):
        with open(path, "w") as f:
            json.dump(asdict(self), f, indent=2)

    @staticmethod
    def load(path: str):
        with open(path) as f:
            data = json.load(f)
        return ExecutionTrace(
            contract_version=data["contract_version"],
            timestamp=data["timestamp"],
            nodes=[NodeTrace(**n) for n in data["nodes"]],
            manifest_hash=data.get("manifest_hash"),
        )


def run_node(name: str, fn, input_data: dict, trace_nodes: List[NodeTrace]) -> dict:
    start = time.time()

    try:
        output = fn(**input_data)
        status = "ok"
    except Exception as e:
        output = {"error": str(e)}
        status = "fail"

    duration = (time.time() - start) * 1000

    trace_nodes.append(
        NodeTrace(
            name=name,
            input=input_data,
            output=output,
            status=status,
            duration_ms=duration,
        )
    )

    return output


def capture_trace(contract_version: str, nodes: List[NodeTrace], manifest_hash: Optional[str] = None) -> ExecutionTrace:
    return ExecutionTrace(
        contract_version=contract_version,
        timestamp=time.time(),
        nodes=nodes,
        manifest_hash=manifest_hash,
    )