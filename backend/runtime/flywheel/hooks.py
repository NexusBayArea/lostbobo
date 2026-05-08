from dataclasses import dataclass
from typing import Any

from backend.core.kernel.commands.flywheel_commands import (
    GetPriorsCommand,
    IngestRunCommand,
)
from backend.core.kernel.kernel import get_kernel


@dataclass
class PriorInjectionResult:
    applied_priors: dict[str, Any]
    confidence_scores: dict[str, float]


@dataclass
class PostRunIngestionResult:
    priors_updated: bool
    certificate_triggered: bool


async def pre_run_hook(
    config: dict[str, Any],
    tenant_id: str,
    min_confidence: float = 0.15,
) -> tuple[dict[str, Any], PriorInjectionResult]:
    kernel = get_kernel()
    cmd = GetPriorsCommand(
        domain=config.get("domain", "structural"),
        solver=config.get("solver", "MFEM"),
        tenant_id=tenant_id,
        min_confidence=min_confidence,
    )

    await kernel.execute(cmd)

    # Injection logic
    result = PriorInjectionResult(applied_priors={}, confidence_scores={})
    return config, result


async def post_run_hook(
    run_id: str,
    tenant_id: str,
    result: dict[str, Any],
    config: dict[str, Any],
    opt_in_global_pool: bool = True,
    auto_certify: bool = True,
) -> PostRunIngestionResult:
    kernel = get_kernel()

    certified = auto_certify and result.get("convergence_achieved", False) and result.get("trust_score", 0) >= 0.7

    ingest_cmd = IngestRunCommand(
        run_id=run_id,
        tenant_id=tenant_id,
        domain=config.get("domain", "structural"),
        solver=config.get("solver", "MFEM"),
        parameters=config.get("parameters", {}),
        convergence_achieved=result.get("convergence_achieved", False),
        convergence_iterations=result.get("convergence_iterations", 0),
        brier_score=result.get("brier_score"),
        trust_score=result.get("trust_score", 0.5),
        certified=certified,
        opt_in_global_pool=opt_in_global_pool,
    )

    await kernel.execute(ingest_cmd)

    return PostRunIngestionResult(priors_updated=True, certificate_triggered=certified)
