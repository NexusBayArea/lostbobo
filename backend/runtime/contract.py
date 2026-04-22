from dataclasses import dataclass, field
from typing import Set, Dict, Any, Optional
import hashlib
import json


@dataclass(frozen=True)
class ExecutionContract:
    version: str
    allowed_modules: Set[str]
    forbidden_imports: Set[str]
    entrypoints: Set[str]
    allowed_roots: Set[str] = field(default_factory=set)

    def validate_manifest(self, manifest: dict[str, Any]) -> bool:
        for node in manifest.get("nodes", {}).values():
            path = node.get("path", "")
            if path and not self.is_allowed_root(path):
                return False
        return True

    def is_allowed_root(self, path: str) -> bool:
        if not self.allowed_roots:
            return True
        root = path.split(".")[0] if "." in path else path
        return root in self.allowed_roots or root in self.allowed_modules

    def is_allowed_import(self, module: str) -> bool:
        if any(module.startswith(f) for f in self.forbidden_imports):
            return False
        root = module.split(".")[0] if "." in module else module
        return root in self.allowed_modules or root in self.allowed_roots


class ContractRegistry:
    def __init__(self):
        self.contracts: Dict[str, ExecutionContract] = {}

    def register(self, contract: ExecutionContract):
        self.contracts[contract.version] = contract

    def get(self, version: str) -> Optional[ExecutionContract]:
        return self.contracts.get(version)

    def latest(self) -> ExecutionContract:
        return self.contracts[max(self.contracts.keys())]

    def validate_compatibility(self, old: str, new: str) -> None:
        a = self.contracts[old]
        b = self.contracts[new]

        removed = a.allowed_modules - b.allowed_modules

        if removed:
            raise RuntimeError(
                f"Incompatible contract change: removed modules {removed}"
            )


CONTRACTS = ContractRegistry()


v1 = ExecutionContract(
    version="v1",
    allowed_modules={"app", "worker", "tools", "scripts", "tests"},
    forbidden_imports={"ci."},
    entrypoints={"app.api.kernel"},
    allowed_roots={"app", "worker", "tools", "scripts", "tests"},
)

CONTRACTS.register(v1)

CONTRACT = CONTRACTS.latest()


def compute_contract(node: dict, upstream_contracts: dict) -> str:
    payload = {
        "type": node["type"],
        "inputs": node.get("inputs", {}),
        "deps": {d: upstream_contracts.get(d) for d in node.get("deps", [])},
    }

    encoded = json.dumps(payload, sort_keys=True).encode()
    return hashlib.sha256(encoded).hexdigest()