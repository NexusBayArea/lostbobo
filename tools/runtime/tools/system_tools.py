from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class SystemTool:
    name: str
    fn: Callable[..., Any]


def register_system_tools(registry: dict[str, SystemTool]) -> None:
    """
    Registers core system tools into the runtime registry.
    Keep minimal: this is the bootstrap-critical layer.
    """

    def echo(x: Any) -> Any:
        return x

    def noop() -> None:
        return None

    registry["echo"] = SystemTool(name="echo", fn=echo)
    registry["noop"] = SystemTool(name="noop", fn=noop)
