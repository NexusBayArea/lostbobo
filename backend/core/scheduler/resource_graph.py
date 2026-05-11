from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.core.scheduler.scheduler_models import ResourceRequest


class ResourceNode:
    def __init__(self, node_id: str, metadata: dict):
        self.node_id = node_id
        self.metadata = metadata
        self.available = metadata.copy()

    def can_fit(self, req: ResourceRequest) -> bool:
        if self.available.get("cpu_cores", 0) < req.cpu_cores:
            return False
        if self.available.get("memory_mb", 0) < req.memory_mb:
            return False
        if req.gpu_fraction > 0:
            if self.available.get("gpu_fraction", 0) < req.gpu_fraction:
                return False
        return True

    def allocate(self, req: ResourceRequest):
        self.available["cpu_cores"] -= req.cpu_cores
        self.available["memory_mb"] -= req.memory_mb
        self.available["gpu_fraction"] -= req.gpu_fraction

    def release(self, req: ResourceRequest):
        self.available["cpu_cores"] += req.cpu_cores
        self.available["memory_mb"] += req.memory_mb
        self.available["gpu_fraction"] += req.gpu_fraction


class ResourceGraph:
    def __init__(self):
        self.nodes: dict[str, ResourceNode] = {}

    def register_node(self, node_id: str, metadata: dict):
        self.nodes[node_id] = ResourceNode(node_id, metadata)

    def available_nodes(self, req: ResourceRequest) -> list[tuple[str, ResourceNode]]:
        candidates = []
        for node_id, node in self.nodes.items():
            if node.can_fit(req):
                candidates.append((node_id, node))
        return candidates
