from pathlib import Path

from backend.runtime.graph import GRAPH
from backend.runtime.manifest import load_manifest


def print_dag_ascii():
    """Beautiful ASCII DAG visualization."""
    print("\n" + "=" * 60)
    print("                    SimHPC EXECUTION DAG")
    print("=" * 60)

    load_manifest()

    order = GRAPH.topological_sort()

    for i, node_id in enumerate(order):
        node = GRAPH.get(node_id)
        deps = node.deps if node.deps else []

        prefix = "|-- " if i < len(order) - 1 else "|-- "
        gpu = " [GPU]" if node.metadata.get("gpu") else ""

        print(f"{prefix}{node_id:25} {gpu}")
        for dep in deps:
            print(f"    +-- depends on: {dep}")

    print("=" * 60)
    print(
        f"Total Nodes: {len(order)} | Contract: {GRAPH.nodes.get(order[0]).metadata.get('contract_version', 'v3.5.1')}\n"
    )


def export_graphviz():
    """Generate Graphviz .dot file for professional visualization."""
    dot = ["digraph SimHPC_DAG {"]
    dot.append('    rankdir="LR";')
    dot.append("    node [shape=box, style=filled, fillcolor=lightblue];")

    for node_id, node in GRAPH.nodes.items():
        label = f"{node_id}\\n{node.metadata.get('type', 'unknown')}"
        dot.append(f'    "{node_id}" [label="{label}"];')

    for node_id, node in GRAPH.nodes.items():
        for dep in node.deps:
            dot.append(f'    "{dep}" -> "{node_id}";')

    dot.append("}")

    Path("dag.gv").write_text("\n".join(dot))
    print("Graphviz file saved as dag.gv")
    print("   Render with: dot -Tpng dag.gv -o dag.png")
