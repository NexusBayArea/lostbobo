from backend.core.kernel.command_bus import command_bus


@command_bus.handler("ANOMALY_DETECT")
async def handle_anomaly_detect(kernel, payload: dict):
    """Kernel-centered entrypoint for Anomaly Detection."""
    service = kernel.services["anomaly_detection"]
    result = await service.detect(payload)

    # Always persist to Supabase
    await kernel.supabase_job_store.record_event(
        "anomaly_check",
        {
            "job_id": payload.get("job_id"),
            "detected": result.detected,
            "severity": result.severity,
            "score": result.score,
            "reason": result.reason,
        },
    )

    return {
        "detected": result.detected,
        "severity": result.severity,
        "score": result.score,
        "reason": result.reason,
        "recommended_action": result.recommended_action,
    }
