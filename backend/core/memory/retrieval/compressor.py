from __future__ import annotations

from backend.core.memory.fabric.semantic_memory import SemanticMemoryRecord


class ContextCompressor:
    async def compress(self, records: list[SemanticMemoryRecord], max_tokens: int = 1024) -> str:
        combined = "\n---\n".join([r.text for r in records])
        if len(combined) > max_tokens * 4:
            combined = combined[: max_tokens * 4]
        return combined
