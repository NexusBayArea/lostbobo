from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from backend.app.kernel.command_bus import command_bus


class TrustRuntimeMiddleware(BaseHTTPMiddleware):
    """
    Enhanced Trust Runtime Middleware with Safety Layer (Loop Prevention).
    Enforces kernel-centered execution + Supabase truth.
    """

    async def dispatch(self, request: Request, call_next):
        # Skip non-agentic / low-risk paths
        if request.url.path in ["/health", "/metrics", "/docs", "/openapi.json"]:
            return await call_next(request)

        tenant_id = request.headers.get("X-Tenant-ID")
        job_id = request.headers.get("X-Job-ID")
        body = {}

        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.json()
            except Exception:
                pass

        # === 1. SAFETY CHECK FIRST (Loop Prevention) ===
        safety_result = await command_bus.route(
            {
                "type": "SAFETY_CHECK_EXECUTION",
                "payload": {
                    "input": body,
                    "tenant_id": tenant_id,
                    "job_id": job_id,
                    "is_agentic": True,
                    "state": body,
                    "is_reflection_step": "reflect" in request.url.path.lower(),
                },
            }
        )

        if not safety_result.safe:
            await command_bus.route(
                {
                    "type": "RECORD_OBSERVABILITY",
                    "payload": {
                        "type": "safety_halt",
                        "reason": safety_result.reason,
                        "action": safety_result.action,
                        "tenant_id": tenant_id,
                    },
                }
            )
            return JSONResponse(
                status_code=429 if safety_result.action == "HALT" else 403,
                content={
                    "error": "Request blocked by Safety Layer",
                    "reason": safety_result.reason,
                    "action": safety_result.action,
                    "trust_decision": "BLOCKED_BY_SAFETY",
                },
            )

        # === 2. TRUST VERIFICATION (only if safety passes) ===
        trust_result = await command_bus.route(
            {
                "type": "TRUST_VERIFY",
                "payload": {"input": body, "tenant_id": tenant_id, "job_id": job_id, "safety_passed": True},
            }
        )

        if trust_result.decision == "BLOCK":
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Request blocked by Trust Runtime",
                    "trust_score": trust_result.trust_score,
                    "risk_flags": trust_result.risk_flags,
                },
            )

        # Proceed with original request
        response = await call_next(request)

        # Attach certificates from both layers
        response.headers["X-Trust-Certificate-ID"] = trust_result.certificate_id or ""
        response.headers["X-Trust-Score"] = str(trust_result.trust_score)
        response.headers["X-Safety-Check"] = "PASSED"

        return response
