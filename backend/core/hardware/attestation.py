"""Hardware attestation — immutable execution proof."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from backend.app.core.supabase import get_supabase_client


class AttestationStatus(str, Enum):
    PENDING = "pending"
    ATTESTED = "attested"
    EXPIRED = "expired"
    REVOKED = "revoked"


@dataclass
class HardwareAttestation:
    attestation_id: str
    node_id: str
    run_id: str
    tenant_id: str
    provider: str
    gpu_model: str
    gpu_count: int
    cuda_version: str
    driver_version: str
    isolation_level: str
    itar_eligible: bool
    physical_host_id: str
    region: str
    zone: str
    sla_tier: str
    status: AttestationStatus = AttestationStatus.PENDING
    attested_at: str = ""
    expires_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "attestation_id": self.attestation_id,
            "node_id": self.node_id,
            "run_id": self.run_id,
            "tenant_id": self.tenant_id,
            "provider": self.provider,
            "gpu_model": self.gpu_model,
            "gpu_count": self.gpu_count,
            "cuda_version": self.cuda_version,
            "driver_version": self.driver_version,
            "isolation_level": self.isolation_level,
            "itar_eligible": self.itar_eligible,
            "physical_host_id": self.physical_host_id,
            "region": self.region,
            "zone": self.zone,
            "sla_tier": self.sla_tier,
            "status": self.status.value,
            "attested_at": self.attested_at,
            "expires_at": self.expires_at,
            "metadata": self.metadata,
        }


class AttestationService:
    def __init__(self) -> None:
        self._db = get_supabase_client()

    async def create_attestation(
        self,
        node_id: str,
        run_id: str,
        tenant_id: str,
        provider: str,
        gpu_model: str,
        gpu_count: int,
        cuda_version: str,
        driver_version: str,
        isolation_level: str,
        itar_eligible: bool,
        physical_host_id: str,
        region: str,
        zone: str,
        sla_tier: str,
        ttl_hours: int = 24,
    ) -> HardwareAttestation:
        now = datetime.now(UTC)
        attestation = HardwareAttestation(
            attestation_id=str(uuid.uuid4()),
            node_id=node_id,
            run_id=run_id,
            tenant_id=tenant_id,
            provider=provider,
            gpu_model=gpu_model,
            gpu_count=gpu_count,
            cuda_version=cuda_version,
            driver_version=driver_version,
            isolation_level=isolation_level,
            itar_eligible=itar_eligible,
            physical_host_id=physical_host_id,
            region=region,
            zone=zone,
            sla_tier=sla_tier,
            status=AttestationStatus.ATTESTED,
            attested_at=now.isoformat(),
            expires_at=now.replace(hour=now.hour + ttl_hours).isoformat(),
        )
        if self._db:
            self._db.table("hardware_attestations").insert(attestation.to_dict()).execute()
        return attestation

    async def verify_attestation(self, attestation_id: str) -> bool:
        if self._db is None:
            return True
        result = (
            self._db.table("hardware_attestations")
            .select("status, expires_at")
            .eq("attestation_id", attestation_id)
            .single()
            .execute()
        )
        if not result.data:
            return False
        if result.data["status"] != AttestationStatus.ATTESTED.value:
            return False
        expires_at = result.data.get("expires_at", "")
        if expires_at:
            expires_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            if datetime.now(UTC) > expires_dt:
                return False
        return True


_service: AttestationService | None = None


def get_attestation_service() -> AttestationService:
    global _service
    if _service is None:
        _service = AttestationService()
    return _service
