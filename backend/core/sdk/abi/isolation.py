from __future__ import annotations

from dataclasses import dataclass, field

from backend.core.sdk.abi.plugin_manifest import IsolationTier

ISOLATION_REQUIREMENTS: dict[IsolationTier, list[str]] = {
    IsolationTier.PROCESS: ["inprocess"],
    IsolationTier.THREAD: ["threadsafe"],
    IsolationTier.CONTAINER: ["container_runtime"],
    IsolationTier.WASM: ["wasm_runtime"],
    IsolationTier.KATA: ["kata_runtime"],
}


@dataclass
class IsolationEnforcement:
    tier: IsolationTier
    requires_sandbox: bool = False
    requires_memory_isolation: bool = False
    requires_filesystem_isolation: bool = False
    requires_network_isolation: bool = False
    permitted_capabilities: list[str] = field(default_factory=list)

    @classmethod
    def for_tier(cls, tier: IsolationTier) -> IsolationEnforcement:
        base = cls(tier=tier)
        if tier == IsolationTier.PROCESS:
            base.requires_sandbox = False
            base.requires_memory_isolation = False
            base.requires_filesystem_isolation = False
            base.requires_network_isolation = False
        elif tier == IsolationTier.THREAD:
            base.requires_sandbox = False
            base.requires_memory_isolation = True
            base.requires_filesystem_isolation = False
            base.requires_network_isolation = False
        elif tier == IsolationTier.CONTAINER:
            base.requires_sandbox = True
            base.requires_memory_isolation = True
            base.requires_filesystem_isolation = True
            base.requires_network_isolation = True
        elif tier == IsolationTier.WASM:
            base.requires_sandbox = True
            base.requires_memory_isolation = True
            base.requires_filesystem_isolation = True
            base.requires_network_isolation = True
        elif tier == IsolationTier.KATA:
            base.requires_sandbox = True
            base.requires_memory_isolation = True
            base.requires_filesystem_isolation = True
            base.requires_network_isolation = True
        return base
