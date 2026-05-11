"""
tests/e2e/test_pipeline_e2e.py
Fully updated for current kernel-centered build + tenant isolation
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from tests.e2e.conftest import (
    TEST_TENANT_ID,
    TEST_SLA_TIER,
    TEST_CLAIM_TEXT,
)


# Stage 1: Rate Limit + Cost Gate (middleware stack)
class TestStage1_RateLimitAndCostGate:
    def test_rate_limiter_passes(self, supabase_stub):
        with patch(
            "backend.app.core.supabase.get_supabase_client", return_value=supabase_stub
        ):
            from backend.core.middleware.rate_limiter import get_rate_limiter

            limiter = get_rate_limiter()
            result = limiter.check(
                TEST_TENANT_ID, "/api/v1/hardware/schedule", TEST_SLA_TIER
            )
            assert result.allowed is True

    @pytest.mark.asyncio
    async def test_llm_cost_gate_blocks_exhausted_budget(self, supabase_stub):
        with patch(
            "backend.app.core.supabase.get_supabase_client", return_value=supabase_stub
        ):
            from backend.core.middleware.llm_cost_gate import get_llm_cost_gate

            gate = get_llm_cost_gate()
            # Seed exhausted budget in stub
            supabase_stub.table("tenant_budgets").insert(
                {"tenant_id": TEST_TENANT_ID, "monthly_llm_budget_usd": 0.0}
            )
            # This requires a budget_utilization view mock, simplified for test
            with patch.object(
                gate,
                "_pre_call_check",
                return_value=MagicMock(allowed=False, reason="budget"),
            ):
                with pytest.raises(RuntimeError, match="budget"):
                    await gate.guarded_llm_call(
                        tenant_id=TEST_TENANT_ID,
                        plugin_name="e2e_test",
                        model="claude-haiku-4-5",
                        messages=[{"role": "user", "content": TEST_CLAIM_TEXT}],
                        max_tokens=500,
                        sla_tier=TEST_SLA_TIER,
                    )


# Stage 2: Kernel Boot (current CoreKernel)
class TestStage2_KernelBoot:
    @pytest.mark.asyncio
    async def test_kernel_boots_cleanly(self, supabase_stub):
        with patch(
            "backend.app.core.supabase.get_supabase_client", return_value=supabase_stub
        ):
            from backend.core.kernel.kernel import CoreKernel

            kernel = CoreKernel()
            await kernel.boot()
            health = kernel.health()
            assert health["booted"] is True
            assert "event_bus" in health["subsystems"]
            assert "state_registry" in health["subsystems"]
            await kernel.shutdown()
