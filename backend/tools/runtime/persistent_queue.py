from pathlib import Path
import json
import threading


class PersistentQueue:
    def __init__(self, path: str = "runtime_queue.json"):
        self.path = Path(path)
        self.lock = threading.Lock()
        self._load()

    def _load(self):
        if self.path.exists():
            self.q = json.loads(self.path.read_text())
        else:
            self.q = []

    def _save(self):
        self.path.write_text(json.dumps(self.q))

    def push(self, task_id: str):
        with self.lock:
            self.q.append(task_id)
            self._save()

    def pop(self):
        with self.lock:
            if not self.q:
                return None
            task_id = self.q.pop(0)
            self._save()
            return task_id

    def snapshot(self):
        return list(self.q)
