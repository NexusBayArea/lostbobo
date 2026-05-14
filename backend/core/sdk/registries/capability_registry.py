from __future__ import annotations

import asyncio
import hashlib
import json
import time
from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from backend.core.sdk.abi.plugin_manifest import GPUProfile


@dataclass(frozen=True)
class InvocationRecord:
    capability: str
    plugin_name: str
    tenant_id: str
    inputs_hash: str
    outputs_hash: str | None = None
    deterministic: bool = False
    seed: int | None = None
    started_at: float = field(default_factory=time.monotonic)
    finished_at: float | None = None
    status: str = "pending"
    error: str | None = None
    invocation_id: str = field(default_factory=lambda: _generate_invocation_id())


def _generate_invocation_id() -> str:
    import uuid

    return uuid.uuid4().hex


@dataclass
class CapabilityEntry:
    name: str
    handler: Callable[..., Awaitable[Any]]
    plugin_name: str
    version: str = "1.0.0"
    deterministic: bool = False
    idempotent: bool = True
    timeout_seconds: int = 300
    max_retries: int = 0
    required_gpu_profile: GPUProfile = GPUProfile.NONE
    estimated_memory_mb: int = 256
    input_schema: dict[str, Any] | None = None
    output_schema: dict[str, Any] | None = None
    invocation_count: int = 0
    last_invoked: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionContext:
    seed: int | None = None
    replay_mode: bool = False
    parent_invocation_id: str | None = None
    tags: dict[str, str] = field(default_factory=dict)


CapabilityHandler = Callable[[dict], Awaitable[Any]]


class CapabilityRegistry:
    def __init__(self, max_invocation_history: int = 10_000):
        self._handlers: dict[str, CapabilityEntry] = {}
        self._history: list[InvocationRecord] = []
        self._max_history = max_invocation_history
        self._lock = asyncio.Lock()
        self._graph: dict[str, set[str]] = defaultdict(set)
        self._tenant_capability_allowlist: dict[str, set[str]] = {}

    # ----------------------------------------------------------
    # Registration
    # ----------------------------------------------------------

    def register(
        self,
        capability: str,
        handler: CapabilityHandler,
        plugin_name: str = "kernel",
        version: str = "1.0.0",
        deterministic: bool = False,
        idempotent: bool = True,
        timeout_seconds: int = 300,
        max_retries: int = 0,
        input_schema: dict | None = None,
        output_schema: dict | None = None,
        required_gpu_profile: GPUProfile = GPUProfile.NONE,
        estimated_memory_mb: int = 256,
        metadata: dict | None = None,
    ) -> None:
        if capability in self._handlers:
            existing = self._handlers[capability]
            raise CapabilityAlreadyRegisteredError(
                f"Capability '{capability}' already registered by '{existing.plugin_name}'"
            )
        self._handlers[capability] = CapabilityEntry(
            name=capability,
            handler=handler,
            plugin_name=plugin_name,
            version=version,
            deterministic=deterministic,
            idempotent=idempotent,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            input_schema=input_schema,
            output_schema=output_schema,
            required_gpu_profile=required_gpu_profile,
            estimated_memory_mb=estimated_memory_mb,
            metadata=metadata or {},
        )

    def unregister(self, capability: str) -> None:
        self._handlers.pop(capability, None)

    # ----------------------------------------------------------
    # Tenant Policy
    # ----------------------------------------------------------

    def set_tenant_capabilities(self, tenant_id: str, allowed: set[str]) -> None:
        self._tenant_capability_allowlist[tenant_id] = allowed

    def tenant_may_invoke(self, tenant_id: str, capability: str) -> bool:
        if tenant_id not in self._tenant_capability_allowlist:
            return True
        return capability in self._tenant_capability_allowlist[tenant_id]

    # ----------------------------------------------------------
    # Invocation
    # ----------------------------------------------------------

    async def invoke(
        self,
        capability: str,
        payload: dict[str, Any],
        *,
        tenant_id: str = "default",
        caller_plugin: str | None = None,
        execution_context: ExecutionContext | None = None,
        timeout_override: int | None = None,
    ) -> Any:
        if not self.tenant_may_invoke(tenant_id, capability):
            raise CapabilityPermissionDeniedError(f"Tenant '{tenant_id}' not authorized to invoke '{capability}'")

        entry = self._handlers.get(capability)
        if not entry:
            raise CapabilityNotFoundError(f"Capability '{capability}' not registered")

        if caller_plugin and caller_plugin != entry.plugin_name:
            self._check_cross_plugin_permissions(caller_plugin, capability)

        if entry.input_schema:
            self._validate_payload(payload, entry.input_schema)

        inputs_hash = self._hash_payload(payload)
        inv_record = InvocationRecord(
            capability=capability,
            plugin_name=entry.plugin_name,
            tenant_id=tenant_id,
            inputs_hash=inputs_hash,
            deterministic=entry.deterministic,
            seed=execution_context.seed if execution_context else None,
        )
        self._record_history(inv_record)

        if entry.deterministic:
            self._set_deterministic_seed(execution_context, inv_record)

        effective_timeout = timeout_override or entry.timeout_seconds
        last_error: Exception | None = None
        for _ in range(entry.max_retries + 1):
            try:
                result = await asyncio.wait_for(
                    entry.handler(payload),
                    timeout=effective_timeout,
                )
                if entry.output_schema:
                    self._validate_payload(result, entry.output_schema, is_output=True)

                self._finalize_invocation_record(
                    inv_record,
                    status="success",
                    outputs_hash=self._hash_payload(result),
                )
                entry.invocation_count += 1
                entry.last_invoked = datetime.now(UTC)
                return result

            except TimeoutError:
                last_error = CapabilityTimeoutError(f"Capability '{capability}' timed out after {effective_timeout}s")
                if not entry.idempotent:
                    break
            except Exception as e:
                last_error = e
                if not entry.idempotent:
                    break

        self._finalize_invocation_record(
            inv_record,
            status="error" if not isinstance(last_error, CapabilityTimeoutError) else "timeout",
            error=str(last_error),
        )
        raise last_error  # type: ignore[misc]

    # ----------------------------------------------------------
    # Replay & History
    # ----------------------------------------------------------

    def get_invocation_history(self, capability: str | None = None) -> list[InvocationRecord]:
        if capability:
            return [r for r in self._history if r.capability == capability]
        return list(self._history)

    def replay_invocation(self, invocation_id: str) -> dict[str, Any]:
        for record in self._history:
            if record.invocation_id == invocation_id:
                if record.status != "success":
                    raise ReplayError(f"Invocation {invocation_id} not successful, cannot replay")
                return {
                    "capability": record.capability,
                    "inputs_hash": record.inputs_hash,
                    "outputs_hash": record.outputs_hash,
                    "deterministic": record.deterministic,
                }
        raise ReplayError(f"Invocation {invocation_id} not found in history")

    # ----------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------

    def _check_cross_plugin_permissions(self, caller_plugin: str, capability: str) -> None:
        pass

    def _validate_payload(
        self,
        payload: dict[str, Any],
        schema: dict[str, Any],
        is_output: bool = False,
    ) -> None:
        pass

    @staticmethod
    def _hash_payload(obj: Any) -> str:
        canonical = json.dumps(obj, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()

    def _set_deterministic_seed(
        self,
        ctx: ExecutionContext | None,
        record: InvocationRecord,
    ) -> None:
        if ctx and ctx.seed is not None:
            import random

            random.seed(ctx.seed)

    def _record_history(self, record: InvocationRecord) -> None:
        if len(self._history) >= self._max_history:
            self._history.pop(0)
        self._history.append(record)

    def _finalize_invocation_record(
        self,
        record: InvocationRecord,
        status: str,
        outputs_hash: str | None = None,
        error: str | None = None,
    ) -> None:
        for i, r in enumerate(self._history):
            if r.invocation_id == record.invocation_id:
                self._history[i] = InvocationRecord(
                    capability=r.capability,
                    plugin_name=r.plugin_name,
                    tenant_id=r.tenant_id,
                    inputs_hash=r.inputs_hash,
                    outputs_hash=outputs_hash,
                    deterministic=r.deterministic,
                    seed=r.seed,
                    started_at=r.started_at,
                    finished_at=time.monotonic(),
                    status=status,
                    error=error,
                    invocation_id=r.invocation_id,
                )
                return

    # ----------------------------------------------------------
    # Query
    # ----------------------------------------------------------

    def get_entry(self, capability: str) -> CapabilityEntry | None:
        return self._handlers.get(capability)

    def list_by_plugin(self, plugin_name: str) -> list[CapabilityEntry]:
        return [e for e in self._handlers.values() if e.plugin_name == plugin_name]

    def add_dependency(self, source: str, target: str) -> None:
        self._graph[source].add(target)

    def capability_graph(self) -> dict[str, set[str]]:
        return dict(self._graph)

    @property
    def registered_capabilities(self) -> list[str]:
        return list(self._handlers.keys())

    def list_capabilities(self) -> list[str]:
        return list(self._handlers.keys())

    def validate(
        self,
        capabilities: list[str],
        allowed_permissions: list[str],
    ) -> list[str]:
        invalid = [c for c in capabilities if c not in allowed_permissions]
        if invalid:
            raise ValueError(f"Capabilities {invalid} not declared in passport permissions")
        return capabilities


# ============================================================
# Exceptions
# ============================================================


class CapabilityError(Exception):
    pass


class CapabilityNotFoundError(CapabilityError):
    pass


class CapabilityAlreadyRegisteredError(CapabilityError):
    pass


class CapabilityPermissionDeniedError(CapabilityError):
    pass


class CapabilityTimeoutError(CapabilityError):
    pass


class CapabilitySchemaValidationError(CapabilityError):
    pass


class CapabilityExecutionError(CapabilityError):
    pass


class ReplayError(CapabilityError):
    pass
