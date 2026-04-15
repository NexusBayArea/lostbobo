from pathlib import Path


class Contract:
    def __init__(self):
        self.root = Path(".").resolve()
        self.paths = {
            "trace": self.root / "runtime_trace.json",
            "state": self.root / "runtime_state.json",
        }

CONTRACT = Contract()
    """
    SINGLE SOURCE OF TRUTH for system architecture.
    """

    def __init__(self):
        # runtime entrypoints
        self.entrypoints = [
            "app.api.kernel",
        ]

        # allowed internal domains
        self.allowed_roots = {
            "app",
            "worker",
            "tests",
            "scripts",
            "tools",
        }

        # forbidden cross-module imports
        self.forbidden_prefixes = {
            "ci.",
        }

        # worker isolation rule (IMPORTANT FIX)
        self.worker_is_isolated = True

    def is_allowed_import(self, module: str) -> bool:
        for bad in self.forbidden_prefixes:
            if module.startswith(bad):
                return False
        return True

    def is_allowed_root(self, path: str) -> bool:
        return any(root in path for root in self.allowed_roots)


CONTRACT = Contract()
