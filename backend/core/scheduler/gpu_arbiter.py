from __future__ import annotations

import asyncio
from dataclasses import dataclass

from backend.core.scheduler.resource_pool import ResourcePool
from backend.core.sdk.abi.plugin_manifest import GPUProfile


@dataclass
class GPUAllocation:
    gpu_id: int
    profile: GPUProfile
    memory_mb: int
    mig_slice_id: str | None = None
    mps_fraction: float | None = None


class GPUArbiter:
    def __init__(self, resource_pool: ResourcePool):
        self.pool = resource_pool
        self._allocations: dict[str, GPUAllocation] = {}
        self._lock = asyncio.Lock()

    async def request(
        self,
        profile: GPUProfile,
        tenant_id: str,
        estimated_memory_mb: int = 256,
    ) -> GPUAllocation:
        async with self._lock:
            if tenant_id in self._allocations:
                return self._allocations[tenant_id]

            if profile == GPUProfile.NONE:
                alloc = GPUAllocation(gpu_id=-1, profile=profile, memory_mb=0)
                self._allocations[tenant_id] = alloc
                return alloc

            if profile in {
                GPUProfile.SHARED_SMALL,
                GPUProfile.SHARED_MEDIUM,
                GPUProfile.SHARED_LARGE,
            }:
                alloc = await self._allocate_mps(profile, estimated_memory_mb)
            elif profile in {GPUProfile.MIG_QUARTER, GPUProfile.MIG_HALF, GPUProfile.MIG_FULL}:
                alloc = await self._allocate_mig(profile, estimated_memory_mb)
            elif profile in {GPUProfile.DEDICATED_SINGLE, GPUProfile.DEDICATED_MULTI}:
                alloc = await self._allocate_dedicated(profile, estimated_memory_mb)
            else:
                raise GPUAllocationFailedError(f"Unknown GPU profile: {profile}")

            if alloc is None:
                raise GPUAllocationFailedError(f"Cannot allocate GPU profile {profile.value} for '{tenant_id}'")
            self._allocations[tenant_id] = alloc
            return alloc

    async def release(self, tenant_id: str) -> None:
        async with self._lock:
            alloc = self._allocations.pop(tenant_id, None)
            if alloc and alloc.gpu_id >= 0:
                await self.pool.release_gpu(alloc.gpu_id)

    async def _allocate_mps(self, profile: GPUProfile, memory_mb: int) -> GPUAllocation | None:
        fraction_map = {
            GPUProfile.SHARED_SMALL: 0.25,
            GPUProfile.SHARED_MEDIUM: 0.50,
            GPUProfile.SHARED_LARGE: 0.75,
        }
        gpus = await self.pool.get_available_gpus(min_memory_mb=memory_mb)
        if gpus:
            gpu = gpus[0]
            await self.pool.allocate_gpu(gpu.id, "mps", memory_mb)
            return GPUAllocation(
                gpu_id=gpu.id,
                profile=profile,
                memory_mb=memory_mb,
                mps_fraction=fraction_map[profile],
            )
        return None

    async def _allocate_mig(self, profile: GPUProfile, memory_mb: int) -> GPUAllocation | None:
        gpus = await self.pool.get_available_gpus(min_memory_mb=memory_mb)
        for gpu in gpus:
            if gpu.mig_enabled:
                await self.pool.allocate_gpu(gpu.id, "mig", memory_mb)
                return GPUAllocation(
                    gpu_id=gpu.id,
                    profile=profile,
                    memory_mb=memory_mb,
                )
        return None

    async def _allocate_dedicated(self, profile: GPUProfile, memory_mb: int) -> GPUAllocation | None:
        gpus = await self.pool.get_available_gpus(min_memory_mb=memory_mb)
        if gpus:
            gpu = gpus[0]
            await self.pool.allocate_gpu(gpu.id, "dedicated", memory_mb)
            return GPUAllocation(gpu_id=gpu.id, profile=profile, memory_mb=memory_mb)
        return None


class GPUAllocationFailedError(Exception):
    pass
