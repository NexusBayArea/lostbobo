import pytest
from unittest.mock import AsyncMock, patch

from backend.runtime.swarm.swarm_coordinator import SwarmCoordinator
from backend.runtime.orchestrator.speculative_orchestrator import (
    SpeculativeOrchestrator,
)
from backend.runtime.chaos_monkey import chaos_monkey
from backend.runtime.fallback import FallbackResult


@pytest.fixture
async def swarm_coordinator():
    coord = SwarmCoordinator()
    # Mock dependencies
    coord._run_aggregated_forecast = AsyncMock()
    return coord


@pytest.mark.asyncio
async def test_full_swarm_under_chaos_primary_success(swarm_coordinator):
    """Full swarm succeeds normally."""
    chaos_monkey.config.enabled = False

    question = {"query": "Test forecasting question"}
    result = await swarm_coordinator.evaluate(question)

    assert result["decision"] in ["PROCEED", "ABORT_LOW_CONFIDENCE"]
    assert result.get("confidence_interval") is not None


@pytest.mark.asyncio
async def test_full_swarm_genai_chaos_fallback(swarm_coordinator):
    """Full swarm with GenAI chaos → graceful fallback."""
    chaos_monkey.config.enabled = True
    chaos_monkey.config.probability = 1.0  # force chaos

    with patch(
        "backend.runtime.fallback.GenAIFallback.call_llm_with_fallback"
    ) as mock_fallback:
        mock_fallback.return_value = FallbackResult(
            success=True,
            data={"forecast": "Degraded but valid"},
            fallback_used=["rag_deterministic"],
            confidence=0.65,
            degraded=True,
        )

        result = await swarm_coordinator.evaluate({"query": "Energy storage forecast"})

    assert result["status"] == "PROCEED"
    assert result.get("confidence_interval") is not None


@pytest.mark.asyncio
async def test_swarm_with_circuit_breaker_and_retry():
    """E2E: Circuit breaker + retry under repeated failures."""
    orch = SpeculativeOrchestrator()

    with patch(
        "backend.runtime.fallback.GenAIFallback.call_llm_with_fallback"
    ) as mock_fb:
        mock_fb.side_effect = [
            Exception("LLM fail 1"),
            Exception("LLM fail 2"),
            FallbackResult(
                True, {"content": "recovered"}, ["deterministic"], 0.70, True
            ),
        ]

        result = await orch._run_agent_resilient(
            agent=AsyncMock(), query="...", tenant_id="t1", name="test_agent"
        )

    assert result.degraded is True
    assert result.score > 0
