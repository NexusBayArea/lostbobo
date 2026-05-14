from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Syscall(str, Enum):
    MEMORY_READ = "memory.read"
    MEMORY_WRITE = "memory.write"
    MEMORY_EVICT = "memory.evict"

    DAG_EXECUTE = "dag.execute"
    DAG_REGISTER = "dag.register"

    LINEAGE_RECORD = "lineage.record"
    LINEAGE_QUERY = "lineage.query"

    STATE_READ = "state.read"
    STATE_WRITE = "state.write"
    STATE_SNAPSHOT = "state.snapshot"

    EVENT_EMIT = "event.emit"
    EVENT_SUBSCRIBE = "event.subscribe"

    CAPABILITY_INVOKE = "capability.invoke"

    SECRET_READ = "secret.read"


@dataclass(frozen=True)
class PermissionSet:
    allowed_syscalls: set[Syscall] = field(default_factory=set)
    syscall_constraints: dict[Syscall, dict[str, Any]] = field(default_factory=dict)
    network_rules: list = field(default_factory=list)
    secret_scopes: list = field(default_factory=list)
    delegated_capabilities: set[str] = field(default_factory=set)

    def check_syscall(self, syscall: Syscall, args: dict[str, Any] | None = None) -> bool:
        if syscall not in self.allowed_syscalls:
            return False
        if syscall in self.syscall_constraints:
            constraints = self.syscall_constraints[syscall]
            if args and not self._validate_constraints(args, constraints):
                return False
        return True

    @staticmethod
    def _validate_constraints(args: dict, constraints: dict) -> bool:
        for key, allowed in constraints.items():
            if key in args and args[key] != allowed:
                return False
        return True
