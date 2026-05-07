import os
import pytest
from unittest.mock import AsyncMock, patch

from backend.runtime.orchestrator.speculative_orchestrator import (
    SpeculativeOrchestrator,
)
from backend.runtime.fallback import FallbackResult


@pytest.fixture
def orchestrator():
    orch = SpeculativeOrchestrator()
    orch.task_metrics = {}
    return orch


@pytest.mark.asyncio
async def test_orchestrator_primary_llm_success(orchestrator):
    agent = AsyncMock()
    agent.run.return_value = {"result": "success", "confidence": 0.95}

    result = await orchestrator._run_agent_resilient(
        agent=agent, query="test query", tenant_id="t1", name="vector_agent"
    )

    assert result.score > 0.9
    assert not result.degraded
    agent.run.assert_called_once()


@pytest.mark.asyncio
async def test_orchestrator_secondary_fallback(orchestrator):
    agent = AsyncMock()
    agent.run.side_effect = RuntimeError("Primary LLM timeout")
    agent.run_with_secondary_provider = AsyncMock(
        return_value={"result": "secondary", "confidence": 0.75}
    )

    with patch(
        "backend.runtime.fallback.GenAIFallback.call_llm_with_fallback"
    ) as mock_fallback:
        mock_fallback.return_value = FallbackResult(
            success=True,
            data={"result": "secondary", "confidence": 0.75},
            fallback_used=["primary_llm", "secondary_llm"],
            confidence=0.75,
            degraded=True,
        )

        result = await orchestrator._run_agent_resilient(
            agent=agent, query="...", tenant_id="t1", name="graph_agent"
        )

    assert result.degraded is True
    assert "graph_agent" in orchestrator.task_metrics


@pytest.mark.asyncio
async def test_orchestrator_full_deterministic_fallback(orchestrator):
    """Primary + secondary fail → deterministic mode."""
    agent = AsyncMock()
    agent.run.side_effect = Exception("LLM outage")
    agent.run_with_secondary_provider.side_effect = Exception("Secondary failure")

    with patch(
        "backend.runtime.fallback.GenAIFallback.call_llm_with_fallback"
    ) as mock_fallback:
        mock_fallback.return_value = FallbackResult(
            success=True,
            data={"hypothesis": "RAG fallback", "confidence": 0.60},
            fallback_used=["rag_deterministic"],
            confidence=0.60,
            degraded=True,
        )

        result = await orchestrator._run_agent_resilient(
            agent=agent, query="...", tenant_id="t1", name="simulation_agent"
        )

    assert result.degraded is True
    assert len(orchestrator.task_metrics) > 0


@pytest.mark.asyncio
async def test_orchestrator_genai_disabled(orchestrator):
    os.environ["GENAI_ENABLED"] = "false"
    agent = AsyncMock()

    with patch(
        "backend.runtime.fallback.GenAIFallback.call_llm_with_fallback"
    ) as mock_fallback:
        mock_fallback.return_value = FallbackResult(
            success=True,
            data={},
            fallback_used=["rag_deterministic"],
            confidence=0.60,
            degraded=True,
        )

        result = await orchestrator._run_agent_resilient(
            agent=agent, query="...", tenant_id="t1", name="test_agent"
        )

    assert result.degraded is True
    os.environ.pop("GENAI_ENABLED", None)
