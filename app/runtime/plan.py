"""
Execution Plan — Immutable deterministic execution artifact

Created at compile time, executed at runtime.
Guarantees: fixed order, fixed dependencies, no runtime ambiguity.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Callable


@dataclass
class ExecutionPlan:
    order: List[str] = field(default_factory=list)
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    payloads: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        for name in self.order:
            if name not in self.dependencies:
                raise ValueError(f"Missing dependencies for: {name}")
            for dep in self.dependencies[name]:
                if dep not in self.order:
                    raise ValueError(f"Invalid dependency: {dep} -> {name}")

    def __repr__(self) -> str:
        return f"ExecutionPlan(order={self.order})"
