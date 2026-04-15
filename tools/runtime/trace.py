import json
import time
from pathlib import Path
from tools.runtime.contract import CONTRACT

TRACE_FILE = CONTRACT.root / "runtime_trace.json"


class Trace:
    def __init__(self):
        self.data = {
            "start_time": time.time(),
            "nodes": {},
        }

    def start_node(self, name: str):
        self.data["nodes"][name] = {
            "status": "running",
            "start": time.time(),
            "end": None,
            "duration": None,
            "error": None,
            "stdout": None,
            "stderr": None,
            "command": None,
        }

    def end_node(self, name: str, success: bool, result=None):
        node = self.data["nodes"][name]
        node["end"] = time.time()
        node["duration"] = node["end"] - node["start"]
        node["status"] = "success" if success else "failed"

        if result:
            node["stdout"] = result.stdout
            node["stderr"] = result.stderr
            node["command"] = result.args

    def save(self):
        self.data["end_time"] = time.time()
        TRACE_FILE.write_text(json.dumps(self.data, indent=2))
