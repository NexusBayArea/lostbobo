from typing import Any

import structlog

from backend.core.supabase_job_store import SupabaseJobStore
from backend.kernel.kernel import Kernel

log = structlog.get_logger(__name__)


class MemoryTrustWeights:
    """Prevents unverified or low-trust data from becoming high-priority memory."""

    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.supabase = SupabaseJobStore()

    async def validate_write(self, payload: dict[str, Any]) -> bool:
        """Gate memory writes based on trust score."""
        trust_score = payload.get("trust_score", 0.0)
        is_verified = payload.get("verified", False)
        operation = payload.get("operation", "unknown")

        if trust_score < 0.45 and not is_verified:
            log.warning("blocked low-trust memory write", operation=operation, trust_score=trust_score)
            await self.supabase.record_event(
                "memory_write_blocked", {"reason": "low_trust", "trust_score": trust_score, "operation": operation}
            )
            return False

        # Allow write but downgrade priority for marginal trust
        if trust_score < 0.7:
            payload["memory_priority"] = "low"

        return True
