"""Command Bus - handles routing of commands to appropriate handlers."""

from __future__ import annotations

from typing import Dict, Any

from app.kernel.kernel import Kernel


class CommandBus:
    def __init__(self, kernel: Kernel):
        self.kernel = kernel

    async def execute(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a command by routing it to the appropriate handler."""
        command_type = command.get("type")
        payload = command.get("payload", {})

        if command_type == "BUILD_PROMPT":
            return await self.kernel.prompt_stack.build(
                payload["agent_id"], payload["query"], payload.get("mode")
            )
        # For now, we also handle other commands by delegating to the kernel's execute method
        # In a more complex system, we might have specific handlers for each command type.
        return await self.kernel.execute(command)