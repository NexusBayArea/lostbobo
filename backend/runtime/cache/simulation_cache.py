"""Deterministic Simulation Cache — hash-based reuse + ZFP compression."""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass

from backend.app.core.supabase import get_supabase_client

log = logging.getLogger(__name__)


def simulation_hash(params: dict) -> str:
    """Stable canonical hash from all inputs."""
    canonical = json.dumps(params, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()[:32]


@dataclass
class CachedSimulation:
    hash: str
    query: str
    parameters: dict
    solver: str
    outputs: dict
    metadata: dict
    timestamp: float
    zfp_fields: bytes | None = None


class SimulationCache:
    """Redis + Supabase backed cache with ZFP support."""

    def __init__(self):
        self._sb = get_supabase_client()
        self._redis = None

    async def get(self, params: dict) -> CachedSimulation | None:
        """Return cached result or None."""
        h = simulation_hash(params)

        if self._redis:
            data = await self._redis.get(f"sim:{h}")
            if data:
                return CachedSimulation(**json.loads(data))

        if self._sb:
            try:
                resp = self._sb.table("simulation_cache").select("*").eq("hash", h).execute()
                if resp.data:
                    row = resp.data[0]
                    return CachedSimulation(
                        hash=row["hash"],
                        query=row["query"],
                        parameters=row["parameters"],
                        solver=row["solver"],
                        outputs=row["outputs"],
                        zfp_fields=row.get("zfp_fields"),
                        metadata=row["metadata"],
                        timestamp=row["timestamp"],
                    )
            except Exception as e:
                log.warning("Cache get failed: %s", e)
        return None

    async def store(self, params: dict, outputs: dict, zfp_fields: bytes | None = None) -> str:
        """Store result with hash."""
        h = simulation_hash(params)

        entry = {
            "hash": h,
            "query": params.get("query", ""),
            "parameters": params,
            "solver": params.get("solver", "MFEM"),
            "outputs": outputs,
            "zfp_fields": zfp_fields.hex() if zfp_fields else None,
            "metadata": {
                "rag_version": "v2",
                "llm_model": "claude-sonnet",
                "timestamp": time.time(),
            },
            "timestamp": time.time(),
        }

        if self._redis:
            try:
                await self._redis.setex(f"sim:{h}", 86400 * 30, json.dumps(entry))
            except Exception as e:
                log.warning("Redis cache store failed: %s", e)

        if self._sb:
            try:
                self._sb.table("simulation_cache").upsert(entry).execute()
            except Exception as e:
                log.warning("Supabase cache store failed: %s", e)

        log.info("Cache stored: %s", h[:12])
        return h
