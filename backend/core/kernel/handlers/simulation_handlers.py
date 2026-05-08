import logging
from datetime import datetime
from typing import Any

from backend.core.kernel.commands.simulation_commands import (
    CancelSimulationCommand,
    GetSimulationStatusCommand,
    RunSimulationCommand,
)
from backend.core.kernel.kernel import get_kernel
from backend.core.services.observability_service import observability
from backend.core.supabase import get_supabase_client
from backend.core.world_model.service import world_model_service
from backend.physics.engine import physics_engine
from backend.runtime.flywheel.hooks import post_run_hook, pre_run_hook
from backend.security.trust.trust_runtime_service import trust_runtime

logger = logging.getLogger(__name__)


async def handle_run_simulation(cmd: RunSimulationCommand) -> dict[str, Any]:
    """Main simulation execution handler."""
    kernel = get_kernel()
    db = get_supabase_client()

    run_id = cmd.run_id
    tenant_id = cmd.tenant_id
    config = cmd.config.copy()

    try:
        enriched_config, injection_result = await pre_run_hook(config, tenant_id)

        trust_result = await trust_runtime.verify_simulation_request(enriched_config, tenant_id)
        if trust_result.decision == "BLOCK":
            raise PermissionError(f"Trust blocked: {trust_result.reason}")

        await (
            db.table("simulation_runs")
            .insert(
                {
                    "run_id": run_id,
                    "tenant_id": tenant_id,
                    "user_id": cmd.user_id,
                    "status": "RUNNING",
                    "config": enriched_config,
                    "started_at": datetime.utcnow().isoformat(),
                    "priority": cmd.priority,
                }
            )
            .execute()
        )

        observability.increment("simulations_started_total", {"tenant_id": tenant_id})

        await world_model_service.update_from_config(enriched_config, run_id)

        physics_result = await physics_engine.run_simulation(
            config=enriched_config,
            run_id=run_id,
            tenant_id=tenant_id,
        )

        post_result = await post_run_hook(
            run_id=run_id,
            tenant_id=tenant_id,
            result=physics_result,
            config=enriched_config,
        )

        # Auto-issue certificate if qualified
        if post_result.certificate_triggered:
            from backend.core.kernel.commands.certificate_commands import IssueCertificateCommand

            cert_cmd = IssueCertificateCommand(
                run_id=run_id,
                tenant_id=tenant_id,
                tier="TIER_2_PHYSICS",
            )
            await kernel.execute(cert_cmd)

        await (
            db.table("simulation_runs")
            .update(
                {
                    "status": "COMPLETED",
                    "result": physics_result,
                    "completed_at": datetime.utcnow().isoformat(),
                    "convergence_achieved": physics_result.get("convergence_achieved", False),
                    "trust_score": physics_result.get("trust_score", 0.5),
                }
            )
            .eq("run_id", run_id)
            .execute()
        )

        observability.increment("simulations_completed_total", {"tenant_id": tenant_id})

        return {
            "run_id": run_id,
            "status": "COMPLETED",
            "result": physics_result,
            "flywheel_injection": injection_result,
            "flywheel_post": post_result,
            "certificate_issued": post_result.certificate_triggered,
        }

    except Exception as e:
        logger.error(f"❌ Simulation {run_id} failed", exc_info=True)
        observability.increment("simulations_failed_total", {"tenant_id": tenant_id})
        try:
            await post_run_hook(run_id, tenant_id, {"convergence_achieved": False, "trust_score": 0.0}, config)
        except Exception:
            pass

        await (
            db.table("simulation_runs")
            .update(
                {
                    "status": "FAILED",
                    "error": str(e),
                    "completed_at": datetime.utcnow().isoformat(),
                }
            )
            .eq("run_id", run_id)
            .execute()
        )
        raise


async def handle_cancel_simulation(cmd: CancelSimulationCommand) -> dict[str, Any]:
    db = get_supabase_client()
    await (
        db.table("simulation_runs")
        .update({"status": "CANCELLED", "error": cmd.reason, "completed_at": datetime.utcnow().isoformat()})
        .eq("run_id", cmd.run_id)
        .execute()
    )
    return {"status": "cancelled", "run_id": cmd.run_id}


async def handle_get_simulation_status(cmd: GetSimulationStatusCommand) -> dict[str, Any]:
    db = get_supabase_client()
    result = db.table("simulation_runs").select("*").eq("run_id", cmd.run_id).execute()
    return result.data[0] if result.data else {"status": "NOT_FOUND"}


SIMULATION_HANDLERS = {
    RunSimulationCommand: handle_run_simulation,
    CancelSimulationCommand: handle_cancel_simulation,
    GetSimulationStatusCommand: handle_get_simulation_status,
}
