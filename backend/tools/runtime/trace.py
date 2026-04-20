import json
from pathlib import Path

def record(node_id, result, path):
    trace_file = Path(path) / f"{node_id}.json"
    with open(trace_file, "w") as f:
        json.dump(result, f)
