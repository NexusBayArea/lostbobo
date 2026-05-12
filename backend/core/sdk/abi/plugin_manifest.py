from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


# Isolation
class IsolationTier(str, Enum):
    PROCESS = "process"
    CONTAINER = "container"
    WASM = "wasm"
    KATA = "kata"


# GPU Profiles
class GPUProfile(str, Enum):
    NONE = "none"
    SHARED_SMALL = "shared-small"
    SHARED_MEDIUM = "shared-medium"
    DEDICATED_A10 = "dedicated-a10"
    DEDICATED_A100 = "dedicated-a100"
    DEDICATED_H100 = "dedicated-h100"


# Permissions
class PluginPermission(str, Enum):
    DAG_EXECUTE = "dag.execute"
    MEMORY_READ = "memory.read"
    MEMORY_WRITE = "memory.write"
    GPU_ALLOCATE = "gpu.allocate"
    NETWORK_EGRESS = "network.egress"
    STORAGE_READ = "storage.read"
    STORAGE_WRITE = "storage.write"
    KERNEL_EVENTS = "kernel.events"
    LINEAGE_WRITE = "lineage.write"


# DAG Contract
class DAGNodeDefinition(BaseModel):
    node_type: str
    version: str
    description: str | None = None


# Event Subscription
class EventSubscription(BaseModel):
    event: str
    durable: bool = True


# Resource Contract
class ResourceContract(BaseModel):
    cpu_cores: float = 1
    memory_mb: int = 512
    max_runtime_seconds: int = 300
    max_concurrency: int = 1
    gpu_profile: GPUProfile = GPUProfile.NONE


# Memory Contract
class MemoryContract(BaseModel):
    namespace: str
    read_scopes: list[str] = []
    write_scopes: list[str] = []
    ttl_seconds: int | None = None


# Plugin Passport
class PluginPassport(BaseModel):
    plugin_id: str
    publisher: str
    version: str
    public_key: str
    permissions: list[str]  # declared capability permissions
    signature: str  # signature of the manifest body
    trust_anchor: str | None = None


# Plugin Manifest
class PluginManifest(BaseModel):
    name: str
    version: str
    capabilities: list[str]
    dag_nodes: list[DAGNodeDefinition]
    permissions: list[PluginPermission]
    resources: ResourceContract
    isolation: IsolationTier
    memory: MemoryContract
    subscriptions: list[EventSubscription] = []
    lineage_enabled: bool = True
    governance_required: bool = True
    deterministic: bool = True
    passport: PluginPassport | None = None
