from backend.core.kernel.command_bus import command_bus


@command_bus.handler("CERTIFICATE_ISSUE")
async def handle_certificate_issue(kernel, payload: dict):
    issuer = kernel.services["certificate_issuer"]
    cert = await issuer.issue(
        run_id=payload["run_id"], tenant_id=payload["tenant_id"], tier=payload.get("tier", "TIER_2_PHYSICS")
    )
    await kernel.supabase_job_store.record_event(
        "certificate_issued",
        {"certificate_id": cert.certificate_id, "run_id": payload["run_id"], "tier": payload.get("tier")},
    )
    return cert.to_dict()


@command_bus.handler("CERTIFICATE_VERIFY")
async def handle_certificate_verify(kernel, payload: dict):
    verifier = kernel.services["certificate_verifier"]
    if "certificate_id" in payload:
        return await verifier.verify_by_id(payload["certificate_id"])
    return verifier.verify_dict(payload["certificate"])
