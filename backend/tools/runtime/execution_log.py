from pathlib import Path
import json
import time
import threading


class ExecutionLog:
    def __init__(self, path: str = "runtime_trace.json"):
        self.path = Path(path)
        self.lock = threading.Lock()
        self.events = []

    def _flush(self):
        self.path.write_text(json.dumps(self.events, indent=2))

    def log(self, event_type: str, task_id: str, payload=None):
        with self.lock:
            self.events.append(
                {
                    "ts": time.time(),
                    "type": event_type,
                    "task_id": task_id,
                    "payload": payload,
                }
            )
            self._flush()
