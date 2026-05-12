from __future__ import annotations

from backend.core.sdk.abi.plugin_manifest import (
    GPUProfile,
    IsolationTier,
    MemoryContract,
    PluginManifest,
    PluginPermission,
    ResourceContract,
)

manifest = PluginManifest(
    name="lineage-collector",
    version="1.0.0",
    capabilities=[
        "lineage.collect",
        "lineage.query",
    ],
    dag_nodes=[],
    permissions=[
        PluginPermission.LINEAGE_WRITE,
        PluginPermission.KERNEL_EVENTS,
    ],
    resources=ResourceContract(cpu_cores=1, memory_mb=256, gpu_profile=GPUProfile.NONE),
    isolation=IsolationTier.PROCESS,
    memory=MemoryContract(namespace="lineage", read_scopes=["tenant"], write_scopes=["tenant"]),
    deterministic=True,
)
