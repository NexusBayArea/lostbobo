from typing import Any

from backend.core.kernel.kernel import Kernel
from backend.runtime.cognition.cognitive_router import CognitiveRouter
from backend.runtime.cognition.execution_attention_graph import ExecutionAttentionGraph


class CognitiveRuntimeService:
    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.graph = ExecutionAttentionGraph(kernel)
        self.router = CognitiveRouter(kernel)

    async def attend(self, payload: dict[str, Any]) -> Any:
        return await self.graph.attend(payload.get("query", ""), payload.get("job_id", ""))

    async def route(self, payload: dict[str, Any]) -> Any:
        return await self.router.route(payload)

    async def add_node(self, payload: dict[str, Any]) -> Any:
        # payload expected to contain ExecutionNode data
        return await self.graph.add_node(payload["node"], payload["job_id"])
