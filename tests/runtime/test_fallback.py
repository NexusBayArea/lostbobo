import os
from unittest.mock import AsyncMock, patch

import pytest
from backend.runtime.fallback import GenAIFallback, FallbackResult


@pytest.mark.asyncio
async def test_primary_llm_success():
    """Primary LLM call succeeds — no fallback triggered."""

    async def primary():
        return {"hypothesis": "Successful claim", "confidence": 0.95}

    result: FallbackResult = await GenAIFallback.call_llm_with_fallback(
        primary_coro=primary(),
        fallback_fn=AsyncMock(),  # not called
        task_name="test_agent",
    )

    assert result.success is True
    assert result.degraded is False
    assert result.fallback_used == []
    assert result.confidence == 0.95
    assert result.data["hypothesis"] == "Successful claim"


@pytest.mark.asyncio
async def test_secondary_llm_fallback():
    """Primary fails → Secondary succeeds."""

    async def primary():
        raise RuntimeError("Primary LLM timeout")

    async def secondary():
        return {"hypothesis": "Secondary result", "confidence": 0.75}

    result = await GenAIFallback.call_llm_with_fallback(
        primary_coro=primary(), fallback_fn=secondary, task_name="test_agent"
    )

    assert result.success is True
    assert result.degraded is True
    assert "primary_llm" in result.fallback_used
    assert "secondary_llm" in result.fallback_used
    assert result.confidence == 0.75


@pytest.mark.asyncio
async def test_full_deterministic_fallback():
    """Primary + Secondary fail → Deterministic RAG fallback."""

    async def primary():
        raise RuntimeError("Primary failed")

    async def secondary():
        raise ConnectionError("Secondary failed")

    with patch(
        "backend.runtime.fallback.GenAIFallback._deterministic_fallback"
    ) as mock_det:
        mock_det.return_value = {
            "hypothesis": "Cached RAG result",
            "source": "deterministic",
        }

        result = await GenAIFallback.call_llm_with_fallback(
            primary_coro=primary(), fallback_fn=secondary, task_name="test_agent"
        )

    assert result.success is True
    assert result.degraded is True
    assert "rag_deterministic" in result.fallback_used
    assert result.confidence == 0.60
    assert result.data["source"] == "deterministic"


@pytest.mark.asyncio
async def test_genai_explicitly_disabled():
    """GENAI_ENABLED=false forces immediate deterministic fallback."""
    os.environ["GENAI_ENABLED"] = "false"

    async def primary():
        return "should never reach"

    with patch(
        "backend.runtime.fallback.GenAIFallback._deterministic_fallback"
    ) as mock_det:
        mock_det.return_value = {"hypothesis": "Deterministic only"}
        result = await GenAIFallback.call_llm_with_fallback(
            primary_coro=primary(), fallback_fn=AsyncMock(), task_name="disabled_test"
        )

    assert result.degraded is True
    assert "rag_deterministic" in result.fallback_used
    os.environ.pop("GENAI_ENABLED", None)


@pytest.mark.asyncio
async def test_all_fallbacks_fail():
    """All paths fail → exception propagates (for circuit breaker)."""

    async def primary():
        raise RuntimeError("Primary")

    async def secondary():
        raise RuntimeError("Secondary")

    with patch(
        "backend.runtime.fallback.GenAIFallback._deterministic_fallback"
    ) as mock_det:
        mock_det.side_effect = Exception("Deterministic failed")

        with pytest.raises(Exception, match="All fallbacks failed"):
            await GenAIFallback.call_llm_with_fallback(
                primary_coro=primary(), fallback_fn=secondary, task_name="catastrophic"
            )
