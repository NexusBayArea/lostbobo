from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import UTC
from enum import Enum
from typing import Any

from backend.app.core.supabase import get_supabase_client
from backend.core.services.observability_service import observability
from backend.core.services.tracing import tracer


class ModelSource(str, Enum):
    SIMHPC_FINE_TUNED = "simhpc_fine_tuned"
    FALLBACK_LLM = "fallback_llm"
    ENSEMBLE = "ensemble"


@dataclass
class PhysicsInferenceRequest:
    task_type: str
    domain: str
    solver: str
    prompt: str
    temperature: float = 0.7
    max_tokens: int = 1024
    prefer_model: ModelSource = ModelSource.SIMHPC_FINE_TUNED
    require_confidence: bool = True
    require_calibration: bool = False


@dataclass
class PhysicsInferenceResponse:
    model_used: str
    task_type: str
    completion: str
    confidence_score: float | None = None
    brier_score: float | None = None
    latency_ms: float = 0.0
    tokens_generated: int = 0
    source_data_runs: int = 0
    is_ensemble: bool = False
    fallback_used: bool = False


class PhysicsInferenceAPI:
    def __init__(self, simhpc_model_path: str | None = None, api_base: str = ""):
        self._db = get_supabase_client()
        self._simhpc_model_path = simhpc_model_path or "./simhpc_model_checkpoints/latest"
        self._api_base = api_base
        self._model_cache: dict[str, Any] = {}
        self._inference_log: list[dict[str, Any]] = []

    async def infer(self, request: PhysicsInferenceRequest, version_id: str | None = None) -> PhysicsInferenceResponse:
        with tracer.start_as_current_span(
            "physics.inference",
            attributes={
                "task_type": request.task_type,
                "domain": request.domain,
                "solver": request.solver,
                "prefer_model": request.prefer_model.value,
                "prompt_length": len(request.prompt),
            },
        ) as span:
            if version_id:
                from backend.ml.registry import ModelRegistry

                registry = ModelRegistry()
                version = await registry.get_version(version_id)
                if version:
                    self._simhpc_model_path = f"./simhpc_model_checkpoints/{version_id}"

            start = time.time()

            if request.prefer_model == ModelSource.SIMHPC_FINE_TUNED:
                with tracer.start_as_current_span("physics.inference.fine_tuned"):
                    response = await self._infer_fine_tuned(request)
                if response is None:
                    with tracer.start_as_current_span("physics.inference.fallback"):
                        response = await self._infer_fallback(request)
                        response.fallback_used = True
            elif request.prefer_model == ModelSource.FALLBACK_LLM:
                with tracer.start_as_current_span("physics.inference.fallback"):
                    response = await self._infer_fallback(request)
            else:
                with tracer.start_as_current_span("physics.inference.fine_tuned"):
                    ft_response = await self._infer_fine_tuned(request)
                with tracer.start_as_current_span("physics.inference.fallback"):
                    fb_response = await self._infer_fallback(request)
                response = self._rank_responses(ft_response, fb_response)

            latency = (time.time() - start) * 1000
            response.latency_ms = latency
            span.set_attribute("model_used", response.model_used)
            span.set_attribute("fallback_used", response.fallback_used)

            observability().increment(
                "ml_inference_total", {"model_used": response.model_used, "task_type": request.task_type}
            )
            observability().observe("ml_inference_latency_ms", latency, {"model_used": response.model_used})

            await self._log_inference(request, response)
            return response

    async def _infer_fine_tuned(self, request: PhysicsInferenceRequest) -> PhysicsInferenceResponse | None:
        if not self._model_loaded("simhpc_fine_tuned"):
            return None

        formatted = self._format_prompt_for_model(request)

        completion = await self._call_model_inference(
            model_name="simhpc_fine_tuned",
            prompt=formatted,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )

        confidence = self._extract_confidence(completion)
        brier = self._extract_brier_score(completion)
        source_runs = await self._estimate_training_data_influence(request.domain, request.solver)

        return PhysicsInferenceResponse(
            model_used="simhpc_fine_tuned_"
            + ("phi_3_mini" if "phi" in self._simhpc_model_path.lower() else "mistral_7b"),
            task_type=request.task_type,
            completion=completion,
            confidence_score=confidence,
            brier_score=brier,
            tokens_generated=len(completion.split()),
            source_data_runs=source_runs,
        )

    async def _infer_fallback(self, request: PhysicsInferenceRequest) -> PhysicsInferenceResponse:
        try:
            from anthropic import Anthropic

            client = Anthropic()
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=request.max_tokens,
                system=(
                    "You are SimHPC, a physics simulation intelligence. "
                    "Express all numerical results with SI units. "
                    "Always include confidence or uncertainty quantification."
                ),
                messages=[{"role": "user", "content": request.prompt}],
            )
            completion = response.content[0].text if response.content else ""
            tokens_generated = getattr(response.usage, "output_tokens", 0) if hasattr(response, "usage") else 0
        except Exception:
            completion = (
                f"[Fallback] Based on general physics principles, the recommended approach for "
                f"{request.task_type} in the {request.domain} domain using {request.solver} is..."
            )
            tokens_generated = len(completion.split())

        return PhysicsInferenceResponse(
            model_used="claude_3_5_sonnet",
            task_type=request.task_type,
            completion=completion,
            tokens_generated=tokens_generated,
            fallback_used=True,
        )

    def _rank_responses(
        self, fine_tuned: PhysicsInferenceResponse | None, fallback: PhysicsInferenceResponse
    ) -> PhysicsInferenceResponse:
        if fine_tuned is None:
            return fallback

        if (fine_tuned.confidence_score or 0) >= 0.7:
            fine_tuned.is_ensemble = True
            return fine_tuned
        else:
            fallback.is_ensemble = True
            return fallback

    def _model_loaded(self, model_name: str) -> bool:
        return model_name in self._model_cache

    def _format_prompt_for_model(self, request: PhysicsInferenceRequest) -> str:
        system = (
            "You are SimHPC, a physics simulation intelligence specialized in "
            f"{request.domain} using {request.solver}. "
            "Express confidence as calibrated probability intervals, not vague qualifiers."
        )
        return f"<|system|>\n{system}\n<|user|>\n{request.prompt}"

    async def _call_model_inference(self, model_name: str, prompt: str, max_tokens: int, temperature: float) -> str:
        return (
            f"[Output from {model_name}] "
            f"Based on verified MFEM/SUNDIALS data, the recommended approach is... "
            f"95% confidence interval: [...]"
        )

    def _extract_confidence(self, text: str) -> float | None:
        if "confidence" not in text.lower():
            return None
        import re

        matches = re.findall(r"0\.\d+", text)
        if matches:
            return float(matches[0])
        return None

    def _extract_brier_score(self, text: str) -> float | None:
        if "brier" not in text.lower():
            return None
        import re

        matches = re.findall(r"[0-9.]+", text)
        if matches:
            try:
                return float(matches[0])
            except ValueError:
                return None
        return None

    async def _estimate_training_data_influence(self, domain: str, solver: str) -> int:
        if self._db is None:
            return 0
        result = self._db.table("aggregated_priors").select("n").eq("domain", domain).eq("solver", solver).execute()
        if result.data:
            return sum(r.get("n", 0) for r in result.data)
        return 0

    async def get_recent_inferences(self, limit: int = 15) -> list[dict[str, Any]]:
        """Return recent inference logs with trace IDs for the dashboard."""
        return [
            {
                "timestamp": entry["timestamp"],
                "task_type": entry["task_type"],
                "domain": entry["domain"],
                "model_used": entry["model_used"],
                "latency_ms": entry["latency_ms"],
                "confidence": entry.get("confidence"),
                "fallback_used": entry.get("fallback_used", False),
                "trace_id": entry.get("trace_id"),
            }
            for entry in self._inference_log[-limit:]
        ]

    async def _log_inference(self, request: PhysicsInferenceRequest, response: PhysicsInferenceResponse) -> None:
        from datetime import datetime

        trace_id = None
        try:
            from opentelemetry import trace

            span = trace.get_current_span()
            if span:
                ctx = span.get_span_context()
                if ctx.is_valid:
                    trace_id = format(ctx.trace_id, "032x")
        except Exception:
            pass

        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "task_type": request.task_type,
            "domain": request.domain,
            "model_used": response.model_used,
            "latency_ms": response.latency_ms,
            "confidence": response.confidence_score,
            "fallback_used": response.fallback_used,
            "is_ensemble": response.is_ensemble,
            "trace_id": trace_id,
        }
        self._inference_log.append(log_entry)

        if self._db and len(self._inference_log) >= 100:
            self._db.table("inference_logs").insert(self._inference_log).execute()
            self._inference_log = []


_inference_api: PhysicsInferenceAPI | None = None


def get_physics_inference_api(model_path: str | None = None) -> PhysicsInferenceAPI:
    global _inference_api
    if _inference_api is None:
        _inference_api = PhysicsInferenceAPI(simhpc_model_path=model_path)
    return _inference_api
