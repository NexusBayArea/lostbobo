from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class GPUState(str, Enum):
    FREE = "free"
    ALLOCATED = "allocated"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


@dataclass
class GPU:
    id: int
    name: str
    memory_mb: int
    mig_enabled: bool = False
    mig_slices: list[dict[str, Any]] = field(default_factory=list)
    state: GPUState = GPUState.FREE
    allocated_to: str | None = None
    allocated_memory_mb: int = 0


@dataclass
class ComputeNode:
    id: str
    hostname: str
    cpu_cores: int
    memory_mb: int
    gpus: list[GPU] = field(default_factory=list)


class ResourcePool:
    def __init__(self):
        self.nodes: dict[str, ComputeNode] = {}
        self._lock = asyncio.Lock()

    async def add_node(self, node: ComputeNode) -> None:
        async with self._lock:
            self.nodes[node.id] = node

    async def remove_node(self, node_id: str) -> None:
        async with self._lock:
            self.nodes.pop(node_id, None)

    async def get_available_gpus(self, min_memory_mb: int = 0) -> list[GPU]:
        async with self._lock:
            return [
                gpu
                for node in self.nodes.values()
                for gpu in node.gpus
                if gpu.state == GPUState.FREE and gpu.memory_mb >= min_memory_mb
            ]

    async def allocate_gpu(self, gpu_id: int, tenant_id: str, memory_mb: int) -> bool:
        async with self._lock:
            for node in self.nodes.values():
                for gpu in node.gpus:
                    if gpu.id == gpu_id and gpu.state == GPUState.FREE:
                        gpu.state = GPUState.ALLOCATED
                        gpu.allocated_to = tenant_id
                        gpu.allocated_memory_mb = memory_mb
                        return True
            return False

    async def release_gpu(self, gpu_id: int) -> None:
        async with self._lock:
            for node in self.nodes.values():
                for gpu in node.gpus:
                    if gpu.id == gpu_id:
                        gpu.state = GPUState.FREE
                        gpu.allocated_to = None
                        gpu.allocated_memory_mb = 0
