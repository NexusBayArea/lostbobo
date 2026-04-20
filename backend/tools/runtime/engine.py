from backend.tools.runtime.backends.registry import BACKENDS
from backend.tools.runtime.trace import record

class ExecutionEngine:
    def run_node(self, node, context):
        node_type = node["type"]

        if node_type not in BACKENDS:
            raise RuntimeError(f"No backend for {node_type}")

        backend = BACKENDS[node_type]

        result = backend.execute(node, context)
        record(node["id"], result, context["workspace"])

        return result

def run_dag(nodes, context):
    engine = ExecutionEngine()
    results = {}

    for node in nodes:
        result = engine.run_node(node, context)
        results[node["id"]] = result

    return results
