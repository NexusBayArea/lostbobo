from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

import redis.asyncio as redis

log = logging.getLogger(__name__)


@dataclass
class ResourceCost:
    """Weighted cost per operation"""

    retrieval: int = 1
    embedding: int = 2
    llm_generation: int = 10
    verification: int = 6
    simulation: int = 50
    agent_hop: int = 8


class ComputeGovernance:
    """
    Centralized rate limiting + governance on CPU node.
    Uses Redis for distributed token buckets + sliding windows.
    """

    def __init__(self):
        self.redis = redis.from_url("redis://localhost:6379", decode_responses=True)
        self.cost = ResourceCost()
        self.default_limits = {
            "user_request_rpm": 20,
            "user_request_rph": 200,
            "token_budget_hourly": 500_000,  # tokens
            "max_stream_seconds": 60,
            "max_concurrent_simulations": 2,
            "max_queue_depth": 20,
            "max_agent_hops": 5,
        }

    async def check(self, request: dict[str, Any]) -> dict[str, Any]:
        """Main gateway check — called before every operation"""
        tenant_id = request.get("tenant_id", "public")
        user_id = request.get("user_id", "anonymous")
        operation = request.get("operation", "unknown")  # llm, simulation, stream, agent, etc.

        key_prefix = f"gov:{tenant_id}:{user_id}"

        # A) Basic request rate limiter
        if not await self._check_rate_limit(f"{key_prefix}:requests", self.default_limits["user_request_rpm"], 60):
            return {"allowed": False, "reason": "rate_limit_requests"}

        # B) Token budget limiter
        tokens = request.get("estimated_tokens", 0)
        if tokens > 0 and not await self._check_token_budget(key_prefix, tokens):
            return {"allowed": False, "reason": "token_budget_exceeded"}

        # C) Simulation throttle
        if operation == "simulation":
            if not await self._check_simulation_throttle(tenant_id):
                return {"allowed": False, "reason": "simulation_queue_full"}

        # D) Agent recursion / A2A protection
        if operation == "agent":
            hops = request.get("agent_hops", 0)
            if hops > self.default_limits["max_agent_hops"]:
                return {"allowed": False, "reason": "max_agent_hops_exceeded"}

        # Streaming protection
        if operation == "stream":
            if not await self._check_stream_limits(key_prefix):
                return {"allowed": False, "reason": "stream_timeout"}

        # Weighted cost deduction
        cost = self._get_cost(operation, tokens)
        await self._deduct_tokens(key_prefix, cost)

        return {"allowed": True, "cost": cost}

    async def _check_rate_limit(self, key: str, limit: int, window: int) -> bool:
        """Sliding window rate limit"""
        now = int(time.time())
        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(key, 0, now - window)
        pipe.zadd(key, {str(now): 1})
        pipe.zcard(key)
        _, _, count = await pipe.execute()
        return count <= limit

    async def _check_token_budget(self, key_prefix: str, tokens: int) -> bool:
        """Hourly token budget"""
        key = f"{key_prefix}:tokens"
        current = await self.redis.get(key) or 0
        if int(current) + tokens > self.default_limits["token_budget_hourly"]:
            return False
        await self.redis.incrby(key, tokens)
        await self.redis.expire(key, 3600)  # 1 hour
        return True

    async def _check_simulation_throttle(self, tenant_id: str) -> bool:
        """A40 protection"""
        queue_key = f"sim:queue:{tenant_id}"
        active = await self.redis.llen(queue_key)
        return active < self.default_limits["max_queue_depth"]

    async def _check_stream_limits(self, key_prefix: str) -> bool:
        """Prevent forever-open streams"""
        key = f"{key_prefix}:stream"
        last = await self.redis.get(key) or 0
        if int(time.time()) - int(last) > self.default_limits["max_stream_seconds"]:
            return False
        await self.redis.set(key, int(time.time()))
        return True

    def _get_cost(self, operation: str, tokens: int = 0) -> int:
        if operation == "llm":
            return tokens * self.cost.llm_generation
        if operation == "simulation":
            return self.cost.simulation
        if operation == "agent":
            return self.cost.agent_hop
        return tokens * self.cost.retrieval

    async def _deduct_tokens(self, key_prefix: str, cost: int):
        await self.redis.incrby(f"{key_prefix}:tokens", cost)

    # Priority queue helper
    async def enqueue_simulation(self, hypothesis_id: str, priority: str = "normal"):
        await self.redis.lpush(f"sim:queue:priority:{priority}", hypothesis_id)


# Singleton
_governance: ComputeGovernance | None = None


def get_governance() -> ComputeGovernance:
    global _governance
    if _governance is None:
        _governance = ComputeGovernance()
    return _governance
