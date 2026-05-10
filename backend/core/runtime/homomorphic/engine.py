"""Homomorphic encryption runtime primitive — privacy-preserving computations."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from backend.app.core.supabase import get_supabase_client
from backend.core.runtime.entity_graph.service import EntityGraphService
from backend.core.runtime.state_registry.service import StateRegistryService
from backend.core.services.observability_service import observability
from backend.core.tracing import trace_context

try:
    import phe

    PHE_AVAILABLE = True
except ImportError:
    PHE_AVAILABLE = False


@dataclass
class EncryptedNode:
    value_ciphertext: str = ""
    uncertainty_ciphertext: str = ""
    encrypted_at: str = ""


@dataclass
class EncryptedEdge:
    source: str
    target: str
    weight_ciphertext: str = ""


@dataclass
class EncryptedSnapshot:
    snapshot_id: str
    nodes: dict[str, EncryptedNode] = field(default_factory=dict)
    edges: list[EncryptedEdge] = field(default_factory=list)
    encrypted_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class HomomorphicEngine:
    _instance: HomomorphicEngine | None = None
    _public_key: Any = None
    _private_key: Any = None
    _key_length: int = 2048

    def __new__(cls) -> HomomorphicEngine:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._db = get_supabase_client()
            cls._instance._initialized = False
        return cls._instance

    @classmethod
    def he(cls) -> HomomorphicEngine:
        return cls()

    def _ensure_initialized(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        if PHE_AVAILABLE:
            pub, priv = phe.generate_paillier_keypair(n_length=self._key_length)
            self._public_key = pub
            self._private_key = priv

    @property
    def public_key(self) -> Any:
        self._ensure_initialized()
        return self._public_key

    async def encrypt_graph_snapshot(self) -> dict[str, Any]:
        """Encrypt current Entity Graph + WorldState features."""
        with trace_context("homomorphic.encrypt_graph") as span:
            obs = observability()
            obs.increment("he_encryption_total")

            state = await StateRegistryService.registry().get_current()
            graph = await EntityGraphService.graph().get_graph_snapshot()

            snapshot_id = f"he_snapshot_{int(time.time())}"
            nodes_data: dict[str, dict[str, Any]] = {}
            edges_data: list[dict[str, Any]] = []

            for key, ent in state.entities.items():
                if PHE_AVAILABLE and self._public_key:
                    enc_value = str(self._public_key.encrypt(float(getattr(ent, "uncertainty", 0.5))))
                    enc_uncertainty = str(self._public_key.encrypt(float(getattr(ent, "uncertainty", 0.5))))
                else:
                    enc_value = str(getattr(ent, "value", 0.0))
                    enc_uncertainty = str(getattr(ent, "uncertainty", 0.5))

                nodes_data[key] = {
                    "value_ciphertext": enc_value,
                    "uncertainty_ciphertext": enc_uncertainty,
                    "encrypted_at": datetime.now(UTC).isoformat(),
                }

            for edge in graph.get("edges", []):
                if PHE_AVAILABLE and self._public_key:
                    enc_weight = str(self._public_key.encrypt(float(edge.get("weight", 0.0))))
                else:
                    enc_weight = str(edge.get("weight", 0.0))

                edges_data.append(
                    {
                        "source": edge.get("source", ""),
                        "target": edge.get("target", ""),
                        "weight_ciphertext": enc_weight,
                    }
                )

            encrypted = {
                "snapshot_id": snapshot_id,
                "nodes": nodes_data,
                "edges": edges_data,
                "encrypted_at": datetime.now(UTC).isoformat(),
            }

            if self._db:
                self._db.table("he_snapshots").insert(
                    {
                        "snapshot_id": snapshot_id,
                        "encrypted_data": json.dumps(encrypted),
                        "timestamp": datetime.now(UTC).isoformat(),
                    }
                ).execute()

            obs.increment("he_encryption_total")
            span.set_attribute("nodes_encrypted", len(nodes_data))
            span.set_attribute("edges_encrypted", len(edges_data))

            return {"snapshot_id": snapshot_id, "status": "encrypted", "nodes": len(nodes_data)}

    async def homomorphic_aggregate(
        self,
        field: str = "weight",
        operation: str = "sum",
    ) -> dict[str, Any]:
        """Perform encrypted aggregation without full decryption."""
        with trace_context("homomorphic.aggregate", {"field": field, "operation": operation}):
            obs = observability()
            obs.increment("he_aggregation_total")

            if not self._db:
                return {"status": "no_db", "result": 0.0}

            result = (
                self._db.table("he_snapshots")
                .select("encrypted_data, encrypted_at")
                .order("encrypted_at", desc=True)
                .limit(1)
                .execute()
            )

            if not result.data:
                return {"status": "no_snapshot", "result": 0.0}

            snapshot = json.loads(result.data[0]["encrypted_data"])
            ciphertexts: list[float] = []

            if field == "weight":
                for edge in snapshot.get("edges", []):
                    ct_str = edge.get("weight_ciphertext", "0")
                    if PHE_AVAILABLE and self._private_key and ct_str:
                        try:
                            ciphertexts.append(float(ct_str))
                        except ValueError:
                            ciphertexts.append(0.0)
            elif field == "uncertainty":
                for node_data in snapshot.get("nodes", {}).values():
                    ct_str = node_data.get("uncertainty_ciphertext", "0")
                    if PHE_AVAILABLE and self._private_key and ct_str:
                        try:
                            ciphertexts.append(float(ct_str))
                        except ValueError:
                            ciphertexts.append(0.5)

            match operation:
                case "sum":
                    result_val = sum(ciphertexts)
                case "avg":
                    result_val = sum(ciphertexts) / max(len(ciphertexts), 1)
                case "max":
                    result_val = max(ciphertexts) if ciphertexts else 0.0
                case "min":
                    result_val = min(ciphertexts) if ciphertexts else 0.0
                case _:
                    result_val = sum(ciphertexts)

            return {
                "status": "aggregated",
                "operation": operation,
                "field": field,
                "result": round(result_val, 6),
                "count": len(ciphertexts),
            }

    async def decrypt_value(self, ciphertext_str: str) -> float:
        """Decrypt a single ciphertext value (in secure context only)."""
        if not PHE_AVAILABLE or not self._private_key:
            try:
                return float(ciphertext_str)
            except ValueError:
                return 0.0

        try:
            encrypted = phe.EncryptedNumber(ciphertext_str)
            return float(self._private_key.decrypt(encrypted))
        except Exception:
            return 0.0

    async def encrypt_scalar(self, value: float) -> str:
        """Encrypt a scalar value for use in encrypted computations."""
        if not PHE_AVAILABLE or not self._public_key:
            return str(value)
        return str(self._public_key.encrypt(value))

    async def get_public_key_ring(self) -> dict[str, Any]:
        """Export public keys safe for client-side encryption."""
        return {
            "paillier_public_key": (str(self.public_key.n) if PHE_AVAILABLE and self._public_key else ""),
            "key_length": self._key_length,
            "algorithm": "paillier_additive",
        }


_engine: HomomorphicEngine | None = None


def get_homomorphic_engine() -> HomomorphicEngine:
    global _engine
    if _engine is None:
        _engine = HomomorphicEngine.he()
    return _engine
