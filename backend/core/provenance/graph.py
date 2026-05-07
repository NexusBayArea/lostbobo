"""Provenance Graph — scientific audit trail for every Hypothesis."""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass
from typing import Any

from backend.core.provenance.graph_service import HypothesisGraph

log = logging.getLogger(__name__)


@dataclass
class ProvenanceNode:
    node_id: str
    node_type: str
    data: dict[str, Any]
    parent_ids: list[str]
    timestamp: float

    def __post_init__(self):
        if self.parent_ids is None:
            self.parent_ids = []
        if self.timestamp is None:
            self.timestamp = time.time()


class ProvenanceGraph:
    """Supabase-backed provenance for full reproducibility and audit."""

    def __init__(self):
        self.graph = HypothesisGraph()

    async def add_node(self, node: ProvenanceNode) -> str:
        payload = {
            "node_type": node.node_type,
            "data": node.data,
            "parent_ids": node.parent_ids,
        }
        hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]

        # Use new Graph Service
        await (
            self.graph.client.table("provenance_nodes")
            .insert(
                {
                    "node_id": node.node_id,
                    "node_type": node.node_type,
                    "data": node.data,
                    "parent_ids": node.parent_ids,
                }
            )
            .execute()
        )
        log.info("Provenance node recorded: %s (%s)", node.node_id, node.node_type)
        return node.node_id
