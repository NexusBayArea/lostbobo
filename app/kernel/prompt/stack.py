"""Dynamic Prompt Stack — layered, context-aware prompting."""

from __future__ import annotations

from typing import Dict, Any, List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.kernel.kernel import Kernel
    from app.kernel.workspace.manager import WorkspaceManager

from app.kernel.workspace.manager import WorkspaceManager


class PromptStack:
    def __init__(self, kernel: "Kernel"):
        self.kernel = kernel
        self.workspace_manager = WorkspaceManager(kernel)

    async def build(self, agent_id: str, user_query: str, mode: str = None) -> str:
        """Build layered prompt with stable prefix + dynamic context."""
        ws = await self.workspace_manager.get_or_create(agent_id)
        if mode:
            await self.workspace_manager.update(agent_id, {"mode": mode})

        layers = []

        # Layer 1: Environment (World Model)
        world = await self.kernel.execute({"type": "WORLD_UPDATE", "payload": {}})  # snapshot
        layers.append(f"ENVIRONMENT:\nCurrent world state: {world.get('entities', {})}")

        # Layer 2: Mode
        layers.append(f"MODE: {ws.mode.upper()}")

        # Layer 3: Active Tasks / Goals
        layers.append(f"ACTIVE GOALS:\n{user_query}")

        # Layer 4: Observational Memory (recent signals)
        memory = await self.kernel.execute({
            "type": "MEMORY_QUERY",
            "payload": {"type": "observation", "limit": 5}
        })
        layers.append(f"RECENT OBSERVATIONS:\n{[m.get('insight') for m in memory]}")

        # Layer 5: Skills Available
        skills = await self.kernel.execute({"type": "SKILL_LIST"})  # add command if needed
        layers.append(f"AVAILABLE SKILLS:\n{[s for s in skills]}")

        # Layer 6: Workspace Artifacts
        layers.append(f"WORKSPACE ARTIFACTS: {len(ws.artifacts)} items")

        # Final instruction
        layers.append(f"\nRespond in {ws.mode} mode. Use tools/skills via Kernel only.")

        return "\n\n".join(layers)