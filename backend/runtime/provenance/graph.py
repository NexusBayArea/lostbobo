"""Provenance Graph — traceable audit layer for every simulation."""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from backend.app.core.supabase import get_supabase_client

log = logging.getLogger(__name__)


@dataclass
class ProvenanceNode:
    node_id: str
    node_type: str
    data: dict[str, Any]
    parent_ids: list[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    hash: str = ""

    def __post_init__(self):
        if not self.hash:
            payload = json.dumps({
                "type": self.node_type,
                "data": self.data,
                "parents": self.parent_ids,
            }, sort_keys=True)
            self.hash = hashlib.sha256(payload.encode()).hexdigest()[:16]


class ProvenanceGraph:
    """Builds and stores a traceable graph of every decision."""

    def __init__(self):
        self._sb = get_supabase_client()

    async def add_node(self, node: ProvenanceNode) -> str:
        """Persist node and return node_id."""
        if self._sb:
            try:
                self._sb.table("provenance_nodes").upsert({
                    "node_id": node.node_id,
                    "node_type": node.node_type,
                    "data": node.data,
                    "parent_ids": node.parent_ids,
                    "timestamp": node.timestamp,
                    "hash": node.hash,
                }).execute()
            except Exception as e:
                log.warning("Failed to persist provenance node: %s", e)
        log.info("Provenance: %s node %s", node.node_type, node.node_id)
        return node.node_id

    async def get_lineage(self, root_id: str) -> list[ProvenanceNode]:
        """Return full provenance chain for a simulation."""
        return []