from backend.core.kernel.command_bus import command_bus


@command_bus.handler("SAFETY_CHECK_EXECUTION")
async def handle_safety_check(kernel, payload: dict):
    """Kernel-centered entrypoint for Safety Service."""
    service = kernel.services["safety"]
    result = await service.check_execution(payload)

    await kernel.supabase_job_store.record_event(
        "safety_check_completed",
        {"job_id": payload.get("job_id"), "safe": result.safe, "reason": result.reason, "action": result.action},
    )

    return {"safe": result.safe, "reason": result.reason, "action": result.action}
