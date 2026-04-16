from tools.runtime.graph import GRAPH


class ExecutionEngine:
    def __init__(self):
        self.results = {}

    def run(self, node_id: str):
        node = GRAPH.get(node_id)

        for dep in node.deps:
            if dep not in self.results:
                self.run(dep)

        self.results[node_id] = node.fn()

        return self.results[node_id]


class ReplayEngine:
    def __init__(self, graph, log):
        self.graph = graph
        self.log = log

    def replay(self):
        results = {}

        for entry in self.log:
            node = self.graph.get(entry["node"])
            results[node.id] = node.fn()

        return results
