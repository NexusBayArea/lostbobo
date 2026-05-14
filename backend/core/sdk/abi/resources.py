from __future__ import annotations

from pydantic import BaseModel, Field

from backend.core.sdk.abi.plugin_manifest import GPUProfile


class GPUAllocation(BaseModel):
    device_id: int
    profile: GPUProfile
    memory_mb: int
    compute_fraction: float = 1.0


class CPUAllocation(BaseModel):
    cores: float = Field(default=1.0, ge=0.1)
    numa_node: int | None = None


class MemoryAllocation(BaseModel):
    memory_mb: int = Field(default=512, ge=64)
    hugepages: bool = False


class StorageAllocation(BaseModel):
    storage_mb: int = Field(default=1024, ge=0)
    mount_path: str = "/data"
    ephemeral: bool = True


class ResourceAllocation(BaseModel):
    cpu: CPUAllocation = Field(default_factory=CPUAllocation)
    memory: MemoryAllocation = Field(default_factory=MemoryAllocation)
    gpu: GPUAllocation | None = None
    storage: StorageAllocation = Field(default_factory=StorageAllocation)
