from backend.core.sdk.plugin_manifest import (
    IsolationTier,
    PluginManifest,
    PluginPermission,
)

manifest = PluginManifest(
    name="science",
    version="1.0.0",
    capabilities=[
        "science.reason",
    ],
    dag_nodes=[],
    permissions=[
        PluginPermission.GPU_ALLOCATE,
    ],
    isolation=IsolationTier.KATA,
)