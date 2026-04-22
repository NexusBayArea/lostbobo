from runtime.graph import GRAPH, Node


def register_default_nodes():
    GRAPH.register(Node(id="hello", deps=[], fn=lambda inputs: print("hello world") or 0))
