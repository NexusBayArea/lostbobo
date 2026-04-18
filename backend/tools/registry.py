from importlib import import_module

# The Single Source of Truth for the Beta Foundation
MODULE_MAP = {
    "system_tools": "tools.runtime.tools.system_tools",
    "contract": "tools.runtime.contract",
    "kernel": "tools.runtime.kernel",
    "log": "tools.runtime.execution_log",
    "queue": "tools.runtime.persistent_queue",
    "intelligence": "tools.runtime.execution_intelligence",
    "graph": "tools.runtime.graph",
    "nodes": "tools.runtime.nodes",
}


def load(name: str):
    if name not in MODULE_MAP:
        raise ImportError(f"Unauthorized module access: {name}")
    return import_module(MODULE_MAP[name])


def validate():
    for name, path in MODULE_MAP.items():
        try:
            import_module(path)
        except ImportError as e:
            print(f"❌ FOUNDATION BREACH: {name} missing at {path}")
            raise e
