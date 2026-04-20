import json
from pathlib import Path

def replay(node_id, workspace):
    trace_file = Path(workspace) / f"{node_id}.json"
    with open(trace_file) as f:
        return json.load(f)
