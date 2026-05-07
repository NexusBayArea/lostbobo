from __future__ import annotations

import os
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

import structlog
from tenacity import retry, stop_after_attempt, wait_exponential_jitter

log = structlog.get_logger(__name__)


@dataclass
class FallbackResult:
    success: bool
    data: Any
    fallback_used: list[str]
    confidence: float
    degraded: bool = False


class GenAIFallback:
    """Centralized GenAI fallback strategies for agents."""

    @staticmethod
    def is_genai_disabled() -> bool:
        return os.getenv("GENAI_ENABLED", "true").lower() == "false"

    @staticmethod
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential_jitter(initial=1, jitter=0.5),
        reraise=True,
    )
    async def call_llm_with_fallback(
        primary_coro: Awaitable[Any],
        fallback_fn: Callable[[], Awaitable[Any]],
        task_name: str,
    ) -> FallbackResult:
        """Primary LLM → Secondary → RAG/Cache → Deterministic."""
        fallbacks = []

        try:
            if GenAIFallback.is_genai_disabled():
                raise RuntimeError("GenAI explicitly disabled for testing")

            result = await primary_coro
            return FallbackResult(success=True, data=result, fallback_used=[], confidence=0.95)

        except Exception as e:  # LLM timeout, rate limit, 5xx, etc.
            log.warning("[%s] Primary LLM failed: %s. Trying fallback...", task_name, e)
            fallbacks.append("primary_llm")

            try:
                # Secondary LLM (LiteLLM routing or backup provider)
                secondary_result = await fallback_fn()
                fallbacks.append("secondary_llm")
                return FallbackResult(
                    success=True,
                    data=secondary_result,
                    fallback_used=fallbacks,
                    confidence=0.75,
                    degraded=True,
                )
            except Exception as e2:
                log.warning("[%s] Secondary LLM also failed: %s", task_name, e2)
                fallbacks.append("secondary_llm_failed")

        # Final fallback: RAG + Deterministic
        log.info("[%s] Entering deterministic fallback mode", task_name)
        deterministic_data = await GenAIFallback._deterministic_fallback(task_name)
        fallbacks.append("rag_deterministic")
        return FallbackResult(
            success=True,
            data=deterministic_data,
            fallback_used=fallbacks,
            confidence=0.60,
            degraded=True,
        )

    @staticmethod
    async def _deterministic_fallback(task_name: str) -> dict:
        """Use cached RAG + World Model + Physics templates."""
        from backend.runtime.rag.router import RAGRouter

        rag = RAGRouter()
        cached = await rag.retrieve(f"fallback for {task_name}", tenant_id="public", limit=3)

        return {
            "hypothesis": cached[0] if cached else "Default simulation template",
            "simulation_result": {"status": "degraded", "value": 0.0},
            "source": "deterministic_fallback",
        }
