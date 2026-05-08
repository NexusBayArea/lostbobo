from typing import Any

from backend.app.kernel.command_bus import command_bus


class CognitiveRouter:
    """Dynamic, sparse cognitive routing based on task type."""

    SPECIALIZATIONS = {
        "financial": ["planner", "verifier", "risk_agent", "market_memory"],
        "coding": ["planner", "compiler_feedback", "validator", "patch_agent"],
        "safety": ["risk_agent", "adversary_detector", "provenance_agent"],
        "research": ["retriever", "validator", "memory_agent", "drift_detector"],
        "autonomous": ["memory_agent", "convergence_detector", "safety_gate"],
    }

    def __init__(self, kernel):
        self.kernel = kernel

    async def route(self, payload: dict[str, Any]) -> dict[str, Any]:
        task_type = payload.get("task_type", "general")
        active_agents = self.SPECIALIZATIONS.get(task_type, ["planner", "validator"])

        results = {}
        for agent_name in active_agents:
            # Resulting agent run is dispatched via command bus
            result = await command_bus.route({"type": "AGENT_RUN", "payload": {"agent": agent_name, "input": payload}})
            results[agent_name] = result

        return {"active_paths": active_agents, "results": results}
