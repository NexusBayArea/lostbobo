from dataclasses import dataclass


@dataclass
class Capability:
    name: str
    enabled: bool
    required_files: list[str]


CAPABILITIES = {
    "core": Capability(
        name="core",
        enabled=True,
        required_files=[
            "backend/tools/runtime/kernel.py",
            "backend/tools/runtime/contract_schema.py",
        ],
    ),
    "cache": Capability(
        name="cache",
        enabled=True,
        required_files=[
            "backend/tools/runtime/cache.py",
        ],
    ),
    "signature": Capability(
        name="signature",
        enabled=False,  # <-- SAFE DEFAULT (prevents CI break)
        required_files=[
            "backend/tools/runtime/signature.py",
        ],
    ),
    "state": Capability(
        name="state",
        enabled=False,  # SAFE DEFAULT
        required_files=[
            "backend/tools/runtime/state.py",
        ],
    ),
}
