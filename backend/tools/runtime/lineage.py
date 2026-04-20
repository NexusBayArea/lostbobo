import json
from pathlib import Path

def build_lineage(nodes, contracts):
    lineage = {}
    for n in nodes:
        lineage[n["id"]] = {
            "deps": n.get("deps", []),
            "contract": contracts[n["id"]],
        }
    return lineage

def record(node_id, contract, deps, result, context):
    trace_file = Path(context["workspace"]) / f"{node_id}.json"
    payload = {
        "contract": contract,
        "deps": deps,
        "result": result,
    }
    with open(trace_file, "w") as f:
        json.dump(payload, f)

def load(node_id, path):
    trace_file = Path(path) / f"{node_id}.json"
    if not trace_file.exists():
        return None
    with open(trace_file) as f:
        return json.load(f)
