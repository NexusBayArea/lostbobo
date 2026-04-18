from dataclasses import dataclass
from typing import Callable, Dict


@dataclass
class Tool:
    name: str
    fn: Callable[[dict], int]


class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Tool] = {}

    def register(self, tool: Tool):
        self.tools[tool.name] = tool

    def run(self, name: str, inputs: dict | None = None) -> int:
        if name not in self.tools:
            raise RuntimeError(f"Unknown tool: {name}")

        return self.tools[name].fn(inputs or {})


TOOL_REGISTRY = ToolRegistry()
