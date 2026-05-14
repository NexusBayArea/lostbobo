"""SimHPC Plugin SDK — Public API for plugin developers."""

from backend.core.sdk.abi.lifecycle import LifecycleEvent, LifecycleManager, PluginState
from backend.core.sdk.abi.permissions import PermissionSet, Syscall
from backend.core.sdk.abi.plugin_manifest import (
    DAGNodeDeclaration,
    EventEmission,
    EventSubscription,
    GPUProfile,
    IsolationTier,
    LineageContract,
    MemoryAccessContract,
    NetworkEgressRule,
    PluginManifest,
    PluginPassport,
    PluginPermission,
    PluginPermissions,
    ResourceQuota,
    SecretScope,
    SyscallPermission,
)
from backend.core.sdk.base_plugin import BasePlugin

SDK_VERSION = "1.0.0"

__all__ = [
    "SDK_VERSION",
    "PluginManifest",
    "BasePlugin",
    "IsolationTier",
    "GPUProfile",
    "ResourceQuota",
    "PluginPermissions",
    "SyscallPermission",
    "NetworkEgressRule",
    "SecretScope",
    "DAGNodeDeclaration",
    "EventSubscription",
    "EventEmission",
    "MemoryAccessContract",
    "LineageContract",
    "PluginPermission",
    "PluginPassport",
    "PluginState",
    "LifecycleManager",
    "LifecycleEvent",
    "Syscall",
    "PermissionSet",
]
