from backend.runtime.graph import GRAPH, Node


def compile_ci_graph():
    """Build the CI DAG from registered steps."""
    from tools.ci_steps import api as api_mod
    from tools.ci_steps import boundaries as boundaries_mod
    from tools.ci_steps import lint as lint_mod
    from tools.ci_steps import lockfile as lockfile_mod
    from tools.ci_steps import pruning as pruning_mod

    GRAPH.register(Node(id="lint", deps=[], fn=lint_mod.run))
    GRAPH.register(Node(id="lockfile", deps=["lint"], fn=lockfile_mod.run))
    GRAPH.register(Node(id="pruning", deps=["lockfile"], fn=pruning_mod.run))
    GRAPH.register(Node(id="boundaries", deps=["pruning"], fn=boundaries_mod.run))
    GRAPH.register(Node(id="api_purity", deps=["boundaries"], fn=api_mod.run))

    print(f"[CI] Graph compiled with {len(GRAPH.nodes)} nodes")
    return GRAPH


def run_ci_dag():
    """Execute the full CI pipeline as a DAG."""
    import asyncio

    from backend.runtime.dag_executor import execute_dag

    compile_ci_graph()
    print("[CI] Starting DAG-based CI Pipeline...")

    try:
        asyncio.run(execute_dag())
        print("[CI] DAG completed successfully!")
        return 0
    except Exception as e:
        print(f"[CI] DAG failed: {e}")
        return 1


if __name__ == "__main__":
    exit(run_ci_dag())
