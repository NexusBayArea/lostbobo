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
    name="robustness",
    version="1.0.0",
    capabilities=[
        "engineering.robustness.run",
        "engineering.robustness.status",
    ],
    dag_nodes=[],
    permissions=[
        PluginPermission.MEMORY_WRITE,
        PluginPermission.DAG_EXECUTE,
    ],
    resources=ResourceContract(
        cpu_cores=2,
        memory_mb=512,
        gpu_profile=GPUProfile.NONE,
    ),
    isolation=IsolationTier.CONTAINER,
    memory=MemoryContract(
        namespace="robustness",
        read_scopes=["tenant"],
        write_scopes=["tenant"],
    ),
)
