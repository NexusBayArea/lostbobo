import structlog

from backend.core.supabase_job_store import SupabaseJobStore
from backend.kernel.dag.node import SimulationNode

log = structlog.get_logger(__name__)


class SimulationGraph:
    """Deterministic executable DAG — core of scientific workflows."""

    def __init__(self, kernel):
        self.kernel = kernel
        self.supabase = SupabaseJobStore()
        self.nodes: dict[str, SimulationNode] = {}
        self.edges: dict[str, list[str]] = {}

    def add_node(self, node: SimulationNode):
        self.nodes[node.id] = node

    def connect(self, src_id: str, dst_id: str):
        self.edges.setdefault(src_id, []).append(dst_id)

    async def execute(self, root_id: str, initial_context: dict = None) -> dict:
        context = initial_context or {}
        completed = set()

        async def run(node_id: str):
            if node_id in completed:
                return

            node = self.nodes[node_id]
            if not await node.validate_inputs(context):
                log.error("missing inputs", node_id=node_id)
                return

            result = await node.execute(context)
            context[node_id] = result
            completed.add(node_id)

            # Persist to Supabase
            await self.supabase.record_event("dag_node_executed", {"node_id": node_id, "outputs": result})

            for next_id in self.edges.get(node_id, []):
                await run(next_id)

        await run(root_id)
        return context

    def find_roots(self) -> list[str]:
        all_nodes = set(self.nodes.keys())
        children = set()
        for targets in self.edges.values():
            children.update(targets)
        return list(all_nodes - children)
