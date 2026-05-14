from __future__ import annotations

import asyncio
import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from backend.core.sdk.abi.memory_contracts import (
    MemoryAccessContractV2 as MemoryAccessContract,
)
from backend.core.sdk.abi.memory_contracts import (
    MemoryAccessRequest,
    MemoryAccessResult,
    MemoryFabricInterface,
    MemoryOperation,
    MemoryTier,
)


@dataclass
class MemoryEntry:
    entry_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    key: str = ""
    value: dict[str, Any] = field(default_factory=dict)
    tier: MemoryTier = MemoryTier.EPISODIC
    namespace: str = "default"
    plugin_name: str = ""
    confidence: float = 1.0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None
    embedding: list[float] | None = None
    access_count: int = 0
    last_accessed: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class MemoryAccessDeniedError(Exception):
    pass


class MemoryFabric(MemoryFabricInterface):
    def __init__(self, supabase_client=None, embedding_service=None):
        self._stores: dict[MemoryTier, dict[str, MemoryEntry]] = {tier: {} for tier in MemoryTier}
        self._namespace_index: dict[str, set[str]] = {}
        self._contracts: dict[str, MemoryAccessContract] = {}
        self._lock = asyncio.Lock()
        self.supabase = supabase_client
        self.embedding_service = embedding_service
        self._eviction_task: asyncio.Task | None = None

    async def start(self) -> None:
        self._eviction_task = asyncio.create_task(self._eviction_loop())

    async def stop(self) -> None:
        if self._eviction_task:
            self._eviction_task.cancel()

    async def register_plugin(self, plugin_name: str, contract: MemoryAccessContract) -> None:
        async with self._lock:
            self._contracts[plugin_name] = contract

    async def unregister_plugin(self, plugin_name: str) -> None:
        async with self._lock:
            contract = self._contracts.pop(plugin_name, None)
            if contract and contract.auto_evict_on_plugin_stop:
                await self._evict_plugin_data(plugin_name)

    def register_contract(self, plugin_name: str, contract: MemoryAccessContract) -> None:
        self._contracts[plugin_name] = contract

    def check_access(self, record: Any, plugin_name: str, write: bool = False) -> None:
        pass

    async def _execute(self, request: MemoryAccessRequest, contract: MemoryAccessContract) -> MemoryAccessResult:
        async with self._lock:
            op_map = {
                MemoryOperation.WRITE: self._handle_write,
                MemoryOperation.READ: self._handle_read,
                MemoryOperation.QUERY: self._handle_query,
                MemoryOperation.EVICT: self._handle_evict,
                MemoryOperation.SNAPSHOT: self._handle_snapshot,
                MemoryOperation.RESTORE: self._handle_restore,
            }
            handler = op_map.get(request.operation)
            if not handler:
                return MemoryAccessResult(
                    success=False,
                    operation=request.operation,
                    tier=request.tier,
                    namespace=request.namespace,
                    error=f"Unknown operation: {request.operation}",
                )
            return await handler(request, contract)

    async def _handle_write(self, request: MemoryAccessRequest, contract: MemoryAccessContract) -> MemoryAccessResult:
        if contract.read_only:
            return MemoryAccessResult(
                success=False,
                operation=MemoryOperation.WRITE,
                tier=request.tier,
                namespace=request.namespace,
                error="Plugin has read-only memory access",
            )
        key = request.key or self._generate_key(request.value)
        ttl = contract.namespaces[0].ttl_seconds if contract.namespaces else None
        embedding = None
        if self.embedding_service and request.tier in {
            MemoryTier.SEMANTIC,
            MemoryTier.LONG_TERM,
        }:
            embedding = await self.embedding_service.embed(json.dumps(request.value))
        entry = MemoryEntry(
            key=key,
            value=request.value or {},
            tier=request.tier,
            namespace=request.namespace,
            plugin_name=request.plugin_name,
            confidence=request.confidence_threshold or 1.0,
            expires_at=datetime.now(UTC) + timedelta(seconds=ttl) if ttl else None,
            embedding=embedding,
            metadata=request.metadata or {},
        )
        self._stores[request.tier][key] = entry
        if request.namespace not in self._namespace_index:
            self._namespace_index[request.namespace] = set()
        self._namespace_index[request.namespace].add(key)
        return MemoryAccessResult(
            success=True,
            operation=MemoryOperation.WRITE,
            tier=request.tier,
            namespace=request.namespace,
            data={"key": key},
            ttl_remaining_seconds=ttl,
        )

    async def _handle_read(self, request: MemoryAccessRequest, contract: MemoryAccessContract) -> MemoryAccessResult:
        store = self._stores[request.tier]
        entry = store.get(request.key)
        if not entry:
            return MemoryAccessResult(
                success=False,
                operation=MemoryOperation.READ,
                tier=request.tier,
                namespace=request.namespace,
                error=f"Key '{request.key}' not found",
            )
        if entry.expires_at and datetime.now(UTC) > entry.expires_at:
            del store[request.key]
            return MemoryAccessResult(
                success=False,
                operation=MemoryOperation.READ,
                tier=request.tier,
                namespace=request.namespace,
                error="Entry expired",
            )
        if contract.min_confidence_threshold and entry.confidence < contract.min_confidence_threshold:
            return MemoryAccessResult(
                success=False,
                operation=MemoryOperation.READ,
                tier=request.tier,
                namespace=request.namespace,
                error=f"Confidence {entry.confidence} below threshold {contract.min_confidence_threshold}",
            )
        entry.access_count += 1
        entry.last_accessed = datetime.now(UTC)
        return MemoryAccessResult(
            success=True,
            operation=MemoryOperation.READ,
            tier=request.tier,
            namespace=request.namespace,
            data=entry.value,
            confidence=entry.confidence,
            ttl_remaining_seconds=(
                int((entry.expires_at - datetime.now(UTC)).total_seconds()) if entry.expires_at else None
            ),
        )

    async def _handle_query(self, request: MemoryAccessRequest, contract: MemoryAccessContract) -> MemoryAccessResult:
        ns_keys = self._namespace_index.get(request.namespace, set())
        store = self._stores[request.tier]
        candidates = []
        for key in ns_keys:
            entry = store.get(key)
            if entry and entry.embedding:
                if entry.expires_at and datetime.now(UTC) > entry.expires_at:
                    continue
                if contract.min_confidence_threshold and entry.confidence < contract.min_confidence_threshold:
                    continue
                candidates.append(entry)
        if not candidates:
            return MemoryAccessResult(
                success=True,
                operation=MemoryOperation.QUERY,
                tier=request.tier,
                namespace=request.namespace,
                entries_found=0,
            )
        query_emb = request.query_embedding or await self.embedding_service.embed(json.dumps(request.value))
        scored = sorted(
            ((self._cosine_similarity(query_emb, e.embedding), e) for e in candidates),
            key=lambda x: x[0],
            reverse=True,
        )
        max_results = min(request.max_results, contract.max_retrieved_entries)
        top = scored[:max_results]
        return MemoryAccessResult(
            success=True,
            operation=MemoryOperation.QUERY,
            tier=request.tier,
            namespace=request.namespace,
            data=[{"key": e.key, "value": e.value, "similarity": sim} for sim, e in top],
            entries_found=len(top),
        )

    async def _handle_evict(self, request: MemoryAccessRequest, contract: MemoryAccessContract) -> MemoryAccessResult:
        store = self._stores[request.tier]
        if request.key:
            entry = store.pop(request.key, None)
            if request.namespace in self._namespace_index:
                self._namespace_index[request.namespace].discard(request.key)
            return MemoryAccessResult(
                success=entry is not None,
                operation=MemoryOperation.EVICT,
                tier=request.tier,
                namespace=request.namespace,
            )
        ns_keys = self._namespace_index.get(request.namespace, set())
        for key in list(ns_keys):
            store.pop(key, None)
        self._namespace_index[request.namespace] = set()
        return MemoryAccessResult(
            success=True,
            operation=MemoryOperation.EVICT,
            tier=request.tier,
            namespace=request.namespace,
            entries_found=len(ns_keys),
        )

    async def _handle_snapshot(
        self, request: MemoryAccessRequest, contract: MemoryAccessContract
    ) -> MemoryAccessResult:
        ns_keys = self._namespace_index.get(request.namespace, set())
        store = self._stores[request.tier]
        snap_data: dict[str, Any] = {}
        for key in ns_keys:
            entry = store.get(key)
            if entry:
                snap_data[key] = {
                    "value": entry.value,
                    "confidence": entry.confidence,
                    "created_at": entry.created_at.isoformat(),
                }
        snap_entry = MemoryEntry(
            key=f"snapshot_{request.namespace}_{datetime.now(UTC).isoformat()}",
            value={
                "namespace": request.namespace,
                "tier": request.tier.value,
                "data": snap_data,
            },
            tier=MemoryTier.LONG_TERM,
            namespace=f"{request.plugin_name}.snapshots",
            plugin_name=request.plugin_name,
        )
        self._stores[MemoryTier.LONG_TERM][snap_entry.key] = snap_entry
        return MemoryAccessResult(
            success=True,
            operation=MemoryOperation.SNAPSHOT,
            tier=request.tier,
            namespace=request.namespace,
            data={"snapshot_key": snap_entry.key, "entries": len(snap_data)},
        )

    async def _handle_restore(self, request: MemoryAccessRequest, contract: MemoryAccessContract) -> MemoryAccessResult:
        snap_entry = self._stores[MemoryTier.LONG_TERM].get(request.key)
        if not snap_entry:
            return MemoryAccessResult(
                success=False,
                operation=MemoryOperation.RESTORE,
                tier=request.tier,
                namespace=request.namespace,
                error="Snapshot not found",
            )
        snap_data = snap_entry.value.get("data", {})
        store = self._stores[request.tier]
        restored = 0
        for key, ed in snap_data.items():
            entry = MemoryEntry(
                key=key,
                value=ed["value"],
                tier=request.tier,
                namespace=request.namespace,
                plugin_name=request.plugin_name,
                confidence=ed.get("confidence", 1.0),
            )
            store[key] = entry
            if request.namespace not in self._namespace_index:
                self._namespace_index[request.namespace] = set()
            self._namespace_index[request.namespace].add(key)
            restored += 1
        return MemoryAccessResult(
            success=True,
            operation=MemoryOperation.RESTORE,
            tier=request.tier,
            namespace=request.namespace,
            entries_found=restored,
        )

    async def _eviction_loop(self, interval_seconds: int = 60) -> None:
        while True:
            try:
                await asyncio.sleep(interval_seconds)
                async with self._lock:
                    now = datetime.now(UTC)
                    for store in self._stores.values():
                        expired = [k for k, v in store.items() if v.expires_at and now > v.expires_at]
                        for key in expired:
                            del store[key]
                            for ns_keys in self._namespace_index.values():
                                ns_keys.discard(key)
            except asyncio.CancelledError:
                break

    async def _evict_plugin_data(self, plugin_name: str) -> None:
        for store in self._stores.values():
            to_remove = [k for k, v in store.items() if v.plugin_name == plugin_name]
            for key in to_remove:
                del store[key]
                for ns_keys in self._namespace_index.values():
                    ns_keys.discard(key)

    @staticmethod
    def _generate_key(value: dict[str, Any] | None) -> str:
        canonical = json.dumps(value or {}, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float] | None) -> float:
        if not b:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b, strict=False))
        norm_a = sum(x**2 for x in a) ** 0.5
        norm_b = sum(x**2 for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
