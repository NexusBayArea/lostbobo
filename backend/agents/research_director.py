from typing import Any

from backend.kernel.kernel import Kernel


class ResearchDirector:
    def __init__(self, kernel: Kernel):
        self.kernel = kernel

    async def investigate(self, hypothesis: str) -> dict[str, Any]:
        plan = await self.kernel.command_bus.execute("SCIENTIFIC_PLAN", {"hypothesis": hypothesis})
        results = await self.kernel.command_bus.execute("EXECUTE_DAG", {"graph": plan})
        return await self.kernel.command_bus.execute("SYNTHESIZE_RESULTS", results)
