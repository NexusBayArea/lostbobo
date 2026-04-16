from importlib import import_module

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
    """Fail-fast check for foundation integrity"""
    for name, path in MODULE_MAP.items():
        try:
            import_module(path)
        except ImportError as e:
            print(f"❌ Foundation Breach: Missing module {name} at {path}")
            raise e
