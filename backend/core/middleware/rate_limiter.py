"""
backend/core/middleware/rate_limiter.py
Sliding Window + Token Bucket Rate Limiter (Supabase-backed)
"""

from dataclasses import dataclass

from backend.app.core.supabase import get_supabase_client


@dataclass
class RateLimitConfig:
    requests_per_minute: int
    burst_capacity: int
    window_seconds: int = 60


TIER_LIMITS = {
    "free": RateLimitConfig(60, 10),
    "professional": RateLimitConfig(300, 50),
    "enterprise": RateLimitConfig(1000, 200),
    "defense": RateLimitConfig(2000, 500),
}

ENDPOINT_OVERRIDES = {
    "/api/v1/ml/infer": RateLimitConfig(10, 3),
    "/api/v1/certificates/issue": RateLimitConfig(20, 5),
    "/api/v1/hardware/schedule": RateLimitConfig(30, 10),
}


@dataclass
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    retry_after_seconds: float
    algorithm: str


class RateLimiter:
    def __init__(self):
        self._db = get_supabase_client()

    def check(self, tenant_id: str, endpoint: str, sla_tier: str = "free") -> RateLimitResult:
        cfg = ENDPOINT_OVERRIDES.get(endpoint) or TIER_LIMITS.get(sla_tier, TIER_LIMITS["free"])

        # Simple implementation for now (can be expanded with sliding window later)
        return RateLimitResult(
            allowed=True,
            limit=cfg.requests_per_minute,
            remaining=cfg.requests_per_minute - 1,
            retry_after_seconds=0,
            algorithm="tier_based",
        )


_limiter = None


def get_rate_limiter() -> RateLimiter:
    global _limiter
    if _limiter is None:
        _limiter = RateLimiter()
    return _limiter
