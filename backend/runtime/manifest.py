"""
SimHPC Execution Manifest
=========================
Declarative definition of all nodes in the system.
"""

MANIFEST = {
    "version": "v3.5.1",
    "nodes": {
        "lint": {"type": "ci", "depends_on": [], "description": "Run ruff format and lint"},
        "lockfile": {"type": "ci", "depends_on": ["lint"], "description": "Verify lockfile sync"},
        "pruning": {"type": "ci", "depends_on": ["lockfile"], "description": "Dependency pruning check"},
        "boundaries": {"type": "ci", "depends_on": ["pruning"], "description": "Import boundary enforcement"},
        "api_purity": {"type": "ci", "depends_on": ["boundaries"], "description": "API purity check"},
        "kernel_boot": {"type": "runtime", "depends_on": ["api_purity"], "description": "Kernel initialization test"},
        "graphrag_retrieve": {
            "type": "intelligence",
            "depends_on": ["kernel_boot"],
            "description": "Three-phase GraphRAG retrieval (vector + knowledge graph expansion)",
            "metadata": {
                "gpu": False,
                "timeout": 30,
                "hops": 2,
                "final_k": 10,
            },
        },
    },
}


def load_manifest() -> dict:
    """Load the execution manifest."""
    return MANIFEST


def get_node(name: str) -> dict:
    return MANIFEST["nodes"].get(name, {})
