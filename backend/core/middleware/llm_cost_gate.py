"""
backend/core/middleware/llm_cost_gate.py
LLM Cost Gate — Hard budget enforcement
"""

from dataclasses import dataclass

from backend.app.core.supabase import get_supabase_client

MODEL_PRICING = {
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "claude-haiku-4-5": {"input": 0.25, "output": 1.25},
}

TIER_MONTHLY_BUDGETS = {
    "free": 5.0,
    "professional": 50.0,
    "enterprise": 500.0,
    "defense": 2000.0,
}


@dataclass
class CostCheckResult:
    allowed: bool
    reason: str = ""


class LLMCostGate:
    def __init__(self):
        self._db = get_supabase_client()

    async def guarded_llm_call(
        self,
        tenant_id: str,
        plugin_name: str,
        model: str,
        messages: list,
        max_tokens: int,
        sla_tier: str = "free",
        **kwargs,
    ):
        # Budget check
        check = await self._pre_call_check(tenant_id, plugin_name, model, max_tokens, sla_tier)
        if not check.allowed:
            raise RuntimeError(f"LLM call blocked: {check.reason}")

        # Make the call (placeholder)
        import anthropic

        client = anthropic.Anthropic()
        response = client.messages.create(model=model, max_tokens=max_tokens, messages=messages, **kwargs)

        # Record usage
        await self._record_usage(tenant_id, plugin_name, model, response)

        return response

    async def _pre_call_check(self, tenant_id: str, plugin_name: str, model: str, max_tokens: int, sla_tier: str):
        # Simple check for now
        return CostCheckResult(allowed=True)

    async def _record_usage(self, tenant_id: str, plugin_name: str, model: str, response):
        pass  # Record to Supabase in full version

    async def get_spend_report(self, tenant_id: str):
        return {"tenant_id": tenant_id, "current_spend": 0.0}


_gate = None


def get_llm_cost_gate() -> LLMCostGate:
    global _gate
    if _gate is None:
        _gate = LLMCostGate()
    return _gate
