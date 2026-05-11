import hashlib
import json
import time


class ReplayScheduler:
    def __init__(self):
        self.placements = []  # list of dicts: {workload_id, node_id, gpu_fraction, timestamp}

    def compute_hash(self, workload) -> str:
        payload = json.dumps(workload.model_dump(exclude={"workload_id"}), sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()

    def record_placement(self, workload_id: str, node_id: str, gpu_fraction: float):
        self.placements.append(
            {"workload_id": workload_id, "node_id": node_id, "gpu_fraction": gpu_fraction, "timestamp": time.time()}
        )

    def get_previous_placement(self, workload_id: str) -> dict | None:
        for p in reversed(self.placements):
            if p["workload_id"] == workload_id:
                return p
        return None
