from fastapi import APIRouter

from backend.core.governance.config import get_governance_settings
from backend.core.governance.service import get_governance

router = APIRouter(prefix="/governance", tags=["governance"])


@router.get("/health")
async def governance_health():
    """Returns current live governance configuration and status"""
    settings = get_governance_settings()

    return {
        "status": "healthy",
        "config": {
            "user_request_rpm": settings.USER_REQUEST_RPM,
            "user_request_rph": settings.USER_REQUEST_RPH,
            "token_budget_hourly": settings.TOKEN_BUDGET_HOURLY,
            "max_context_tokens": settings.MAX_CONTEXT_TOKENS,
            "max_stream_seconds": settings.MAX_STREAM_SECONDS,
            "max_concurrent_simulations": settings.MAX_CONCURRENT_SIMULATIONS,
            "max_queue_depth": settings.MAX_QUEUE_DEPTH,
            "max_agent_hops": settings.MAX_AGENT_HOPS,
        },
        "redis_connected": await _check_redis(),
        "active_limits": {
            "simulation_concurrency": settings.MAX_CONCURRENT_SIMULATIONS,
            "token_budget_remaining": "dynamic (see /metrics)",
        },
    }


async def _check_redis() -> bool:
    try:
        gov = get_governance()
        await gov.redis.ping()
        return True
    except Exception:
        return False
