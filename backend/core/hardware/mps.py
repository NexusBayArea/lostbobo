from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass

from typing import TYPE_CHECKING

from backend.core.hardware.pools import ExecutionCapacity

if TYPE_CHECKING:
    from backend.core.hardware.isolation import IsolationConfig
from backend.core.services.observability_service import observability
from backend.core.tracing import trace_context


@dataclass
class MPSConfig:
    active_thread_percentage: int = 95
    max_threads_per_process: int = 64
    memory_limit_mb: int | None = None


class MPSManager:
    """CUDA MPS daemon management and optimization."""

    _instance = None
    _daemons: dict[str, str] = {}  # capacity_id → status

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def manager(cls) -> MPSManager:
        return cls()

    async def start_daemon(self, capacity: ExecutionCapacity, config: IsolationConfig) -> bool:
        """Start optimized MPS daemon for this GPU."""
        with trace_context("mps.start_daemon") as span:
            try:
                env = os.environ.copy()
                gpu_id = getattr(capacity, "node_id", "0")
                env["CUDA_MPS_PIPE_DIRECTORY"] = f"/tmp/nvidia-mps-{gpu_id}"
                env["CUDA_MPS_LOG_DIRECTORY"] = f"/var/log/nvidia-mps-{gpu_id}"
                env["CUDA_MPS_ACTIVE_THREAD_PERCENTAGE"] = str(int(config.compute_limit * 100))

                await asyncio.create_subprocess_exec(
                    "nvidia-cuda-mps-control",
                    "-d",
                    env=env,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await asyncio.sleep(0.8)  # Allow daemon to initialize

                self._daemons[capacity.id] = "running"
                observability().increment("mps_daemons_started")
                span.set_attribute("status", "success")
                return True

            except Exception as e:
                observability().increment("mps_start_failures")
                span.set_attribute("error", str(e))
                return False

    async def shutdown(self, capacity_id: str):
        if capacity_id in self._daemons:
            del self._daemons[capacity_id]
