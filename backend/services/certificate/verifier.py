from typing import Any

from backend.core.supabase_job_store import SupabaseJobStore
from backend.services.certificate.signer import CertificateSigner


class CertificateVerifier:
    """Verifies simulation certificates."""

    def __init__(self):
        self.supabase = SupabaseJobStore()
        self.signer = CertificateSigner()

    async def verify_by_id(self, certificate_id: str) -> dict[str, Any]:
        cert = await self.supabase.get_certificate(certificate_id)
        if not cert:
            return {"valid": False, "reason": "Certificate not found"}

        return self._perform_verification(cert)

    def verify_dict(self, cert: dict[str, Any]) -> dict[str, Any]:
        return self._perform_verification(cert)

    def _perform_verification(self, cert: dict[str, Any]) -> dict[str, Any]:
        # Validate signature
        expected_sig = self.signer.sign(cert["full_certificate"])
        if cert["signature"] != expected_sig:
            return {"valid": False, "reason": "Signature mismatch"}

        return {"valid": True, "details": cert}
