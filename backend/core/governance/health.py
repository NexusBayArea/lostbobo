"""
Startup + Runtime Health Check for Governance Secrets (Infisical)
"""

import logging

from backend.core.governance.config import get_governance_settings

log = logging.getLogger(__name__)


async def validate_governance_secrets() -> dict:
    """Called at startup and exposed on /governance/health"""
    settings = get_governance_settings()

    required_keys = [
        "USER_REQUEST_RPM",
        "USER_REQUEST_RPH",
        "TOKEN_BUDGET_HOURLY",
        "MAX_CONTEXT_TOKENS",
        "MAX_STREAM_SECONDS",
        "MAX_CONCURRENT_SIMULATIONS",
        "MAX_QUEUE_DEPTH",
        "MAX_AGENT_HOPS",
    ]

    missing = []
    for key in required_keys:
        value = getattr(settings, key, None)
        if value is None or (isinstance(value, int | str) and str(value).strip() == ""):
            missing.append(key)

    status = "healthy" if not missing else "degraded"

    if missing:
        log.error(f"❌ Missing governance secrets in Infisical: {missing}")
    else:
        log.info("✅ All governance secrets loaded from Infisical")

    return {
        "status": status,
        "infisical_connected": True,
        "governance_secrets_valid": len(missing) == 0,
        "missing_secrets": missing,
        "active_limits": {
            "user_request_rpm": settings.USER_REQUEST_RPM,
            "token_budget_hourly": settings.TOKEN_BUDGET_HOURLY,
            "max_concurrent_simulations": settings.MAX_CONCURRENT_SIMULATIONS,
            "max_agent_hops": settings.MAX_AGENT_HOPS,
        },
    }
