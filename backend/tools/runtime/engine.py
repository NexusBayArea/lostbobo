from tools.runtime.graph import GRAPH


class ExecutionEngine:
    def __init__(self):
        self.results = {}

    def run_all(self):
        order = GRAPH.topologically_sorted()

        for node_id in order:
            node = GRAPH.get(node_id)

            # ensure deps already computed
            inputs = {d: self.results[d] for d in node.deps}

            self.results[node_id] = node.fn(inputs)

        return self.results
