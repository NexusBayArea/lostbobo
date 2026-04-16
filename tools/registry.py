from importlib import import_module

MODULE_MAP = {
    "system_tools": "tools.runtime.tools.system_tools",
    "ci_compiler": "tools.runtime.ci_compiler",
    "contract": "tools.runtime.contract",
    "deps": "tools.runtime.deps",
    "engine": "tools.runtime.engine",
    "graph": "tools.runtime.graph",
    "manifest": "tools.runtime.manifest",
    "nodes": "tools.runtime.nodes",
    "replay": "tools.runtime.replay",
    "trace": "tools.runtime.trace",
}


def load(name: str):
    if name not in MODULE_MAP:
        raise ImportError(f"Module '{name}' not found in Beta Foundation Registry.")
    return import_module(MODULE_MAP[name])


def validate():
    """Fail-fast check for foundation integrity"""
    for name, path in MODULE_MAP.items():
        try:
            import_module(path)
        except ImportError as e:
            print(f"[FAIL] missing module {name} at {path}")
            raise e
