from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MemoryTier(str, Enum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    EXECUTION = "execution"
    CAUSAL = "causal"
    LONG_TERM = "long_term"


class MemoryOperation(str, Enum):
    READ = "read"
    WRITE = "write"
    EVICT = "evict"
    QUERY = "query"
    SNAPSHOT = "snapshot"
    RESTORE = "restore"


class MemoryAccessPolicy(BaseModel):
    tier: str
    namespace: str
    read_allowed: bool = False
    write_allowed: bool = False
    evict_allowed: bool = False
    ttl_seconds: int | None = None
    confidence_threshold: float | None = Field(default=None, ge=0.0, le=1.0)


class MemoryFabricAccess(BaseModel):
    policies: list[MemoryAccessPolicy] = Field(default_factory=list)
    default_ttl_seconds: int | None = None
    max_namespaces: int = 10


class MemoryKey(BaseModel):
    namespace: str
    key: str
    tier: str = "episodic"


class MemoryEntry(BaseModel):
    key: MemoryKey
    value: bytes
    ttl_seconds: int | None = None
    plugin_source: str = ""


class MemoryNamespace(BaseModel):
    prefix: str
    tier: MemoryTier
    max_entries: int = 10000
    ttl_seconds: int | None = None
    indexing: bool = True


class MemoryAccessContractV2(BaseModel):
    allowed_tiers: list[MemoryTier] = Field(default_factory=list)
    allowed_operations: dict[str, list[MemoryOperation]] = Field(default_factory=dict)
    namespaces: list[MemoryNamespace] = Field(default_factory=list)
    default_namespace: str | None = None
    read_only: bool = False
    allow_cross_namespace_read: bool = False
    allow_cross_namespace_write: bool = False
    min_confidence_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    max_retrieved_entries: int = 100
    auto_evict_on_plugin_stop: bool = True
    snapshot_on_stop: bool = False

    def can_operate(self, tier: MemoryTier, operation: MemoryOperation) -> bool:
        if tier not in self.allowed_tiers:
            return False
        allowed_ops = self.allowed_operations.get(tier.value, [])
        return operation in allowed_ops

    def is_namespace_allowed(self, namespace: str) -> bool:
        for ns in self.namespaces:
            if namespace.startswith(ns.prefix.rstrip("*")):
                return True
        if self.default_namespace and namespace.startswith(self.default_namespace.rstrip("*")):
            return True
        return False


class MemoryAccessRequest(BaseModel):
    plugin_name: str
    namespace: str
    tier: MemoryTier
    operation: MemoryOperation
    key: str | None = None
    value: dict[str, Any] | None = None
    query_embedding: list[float] | None = None
    confidence_threshold: float | None = None
    max_results: int = 10
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemoryAccessResult(BaseModel):
    success: bool
    operation: MemoryOperation
    tier: MemoryTier
    namespace: str
    data: Any = None
    confidence: float | None = None
    entries_found: int = 0
    ttl_remaining_seconds: int | None = None
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemoryFabricInterface:
    async def access(
        self,
        request: MemoryAccessRequest,
        contract: MemoryAccessContractV2,
    ) -> MemoryAccessResult:
        if not contract.can_operate(request.tier, request.operation):
            return MemoryAccessResult(
                success=False,
                operation=request.operation,
                tier=request.tier,
                namespace=request.namespace,
                error=f"Plugin '{request.plugin_name}' not authorized for {request.operation.value} on {request.tier.value}",
            )
        if not contract.is_namespace_allowed(request.namespace):
            return MemoryAccessResult(
                success=False,
                operation=request.operation,
                tier=request.tier,
                namespace=request.namespace,
                error=f"Namespace '{request.namespace}' not allowed by contract",
            )
        if contract.min_confidence_threshold and request.confidence_threshold:
            if request.confidence_threshold < contract.min_confidence_threshold:
                return MemoryAccessResult(
                    success=False,
                    operation=request.operation,
                    tier=request.tier,
                    namespace=request.namespace,
                    error=f"Confidence {request.confidence_threshold} below minimum {contract.min_confidence_threshold}",
                )
        return await self._execute(request, contract)

    async def _execute(
        self,
        request: MemoryAccessRequest,
        contract: MemoryAccessContractV2,
    ) -> MemoryAccessResult:
        raise NotImplementedError
