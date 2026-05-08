from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SimulationNode(ABC):
    id: str
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @abstractmethod
    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """Execute node and return outputs"""
        pass

    async def validate_inputs(self, context: dict[str, Any]) -> bool:
        return all(inp in context for inp in self.inputs)
