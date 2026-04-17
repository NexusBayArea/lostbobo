from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class Contract:
    root: Path = field(default_factory=lambda: Path(".").resolve())

    entrypoints: list[str] = field(
        default_factory=lambda: [
            "app.main",
            "tools.bootstrap",
        ]
    )

    allowed_roots: set[str] = field(
        default_factory=lambda: {
            "app",
            "worker",
            "tests",
            "scripts",
            "tools",
        }
    )

    forbidden_prefixes: set[str] = field(
        default_factory=lambda: {
            "ci.",
        }
    )

    def is_allowed_import(self, module: str) -> bool:
        return not any(module.startswith(bad) for bad in self.forbidden_prefixes)

    def is_allowed_root(self, path: str) -> bool:
        return any(root in path for root in self.allowed_roots)


CONTRACT = Contract()
