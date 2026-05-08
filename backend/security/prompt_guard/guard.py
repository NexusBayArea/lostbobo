from typing import Any


class PromptGuard:
    async def detect(self, prompt: str) -> dict[str, Any]:
        flags = []
        lower = prompt.lower()
        if any(x in lower for x in ["ignore previous", "override", "jailbreak", "system prompt", "disregard"]):
            flags.append("instruction_override")
        if "<|im_start|>" in prompt or any(x in lower for x in ["<script>", "sql injection", "rm -rf"]):
            flags.append("adversarial_payload")
        return {"safe": len(flags) == 0, "flags": flags, "score": max(0.0, 1.0 - len(flags) * 0.4)}
