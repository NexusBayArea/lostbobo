from importlib import import_module

MODULE_MAP = {
    "system_tools": "tools.runtime.tools.system_tools",
    "ci_compiler": "tools.runtime.ci_compiler",
    "ci_graph": "tools.runtime.ci_graph",
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
        raise ImportError(f"Module not registered in MODULE_MAP: {name}")

    return import_module(MODULE_MAP[name])


def validate():
    # fail fast if anything missing
    for name, path in MODULE_MAP.items():
        import_module(path)
