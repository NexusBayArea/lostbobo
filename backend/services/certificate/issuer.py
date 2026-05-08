import hashlib
import uuid

from backend.core.supabase_job_store import SupabaseJobStore
from backend.services.certificate.models import Certificate
from backend.services.certificate.signer import CertificateSigner


class CertificateIssuer:
    """Issues formal simulation certificates."""

    def __init__(self):
        self.supabase = SupabaseJobStore()
        self.signer = CertificateSigner()

    async def issue(self, run_id: str, tenant_id: str, tier: str) -> Certificate:
        # Fetch run results
        run = await self.supabase.get_run_data(run_id)

        payload = {"run_id": run_id, "tenant_id": tenant_id, "result": run.get("result"), "tier": tier}

        cert_hash = hashlib.sha256(str(payload).encode()).hexdigest()
        signature = self.signer.sign(payload)

        cert = Certificate(
            certificate_id=str(uuid.uuid4()),
            run_id=run_id,
            tenant_id=tenant_id,
            certificate_hash=cert_hash,
            signature=signature,
            public_key_fingerprint=self.signer.get_fingerprint(),
            full_certificate=payload,
        )

        await self.supabase.save_certificate(cert.to_dict())
        return cert
