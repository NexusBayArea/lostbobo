"""Planner Agent Example."""

from app.kernel.kernel import Kernel


class PlannerAgent:
    def __init__(self, kernel: Kernel):
        self.kernel = kernel

    async def run(self, input_data: dict):
        prompt = await self.kernel.prompt_stack.build(
            agent_id="planner",
            user_query=input_data.get("query", ""),
            mode=input_data.get("mode", "optimize")
        )
        # Use prompt for LLM call or skill routing...
        return {"prompt_used": prompt[:200] + "...", "result": "planned"}