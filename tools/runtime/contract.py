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

    def validate_manifest(self, manifest: dict) -> bool:
        """
        Validates the system manifest against the defined architectural contract.
        """
        if not isinstance(manifest, dict):
            return False

        # Basic structural validation: in v3.0.0, we expect either nodes or capabilities
        if "nodes" not in manifest and "capabilities" not in manifest:
            # We allow an empty dict as a minimal valid manifest
            return len(manifest) == 0

        # If nodes are present, ensure they don't violate architectural boundaries
        nodes = manifest.get("nodes", {})
        if isinstance(nodes, dict):
            for node_id in nodes:
                if not self.is_allowed_import(node_id):
                    return False

        return True


CONTRACT = Contract()
