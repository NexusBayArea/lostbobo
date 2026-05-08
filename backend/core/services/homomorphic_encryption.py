import base64
import os
from dataclasses import dataclass
from typing import Any

import structlog
import tenseal as ts

from backend.core.supabase_job_store import SupabaseJobStore
from backend.kernel.kernel import Kernel

log = structlog.get_logger(__name__)


@dataclass
class EncryptedPayload:
    ciphertext: str
    context: str
    metadata: dict[str, Any]


class HomomorphicEncryptionService:
    """Kernel-centered Homomorphic Encryption (CKKS) service."""

    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.supabase = SupabaseJobStore()
        self.enabled = os.getenv("HOMOMORPHIC_ENABLED", "false").lower() == "true"

        if self.enabled:
            # CKKS context for approximate arithmetic
            self.context = ts.context(
                ts.SCHEME_TYPE.CKKS, poly_modulus_degree=8192, coeff_mod_bit_sizes=[60, 40, 40, 60]
            )
            self.context.generate_galois_keys()
            self.context.global_scale = 2**40
            log.info("Homomorphic Encryption initialized (CKKS)")
        else:
            self.context = None
            log.info("Homomorphic Encryption disabled (fallback to plaintext)")

    async def encrypt(self, payload: dict[str, Any]) -> EncryptedPayload:
        data = payload["data"]
        job_id = payload["job_id"]

        if not self.enabled or self.context is None:
            plaintext = base64.b64encode(str(data).encode()).decode()
            await self.supabase.record_event("he_fallback", {"job_id": job_id})
            return EncryptedPayload(ciphertext=plaintext, context="plaintext", metadata=data)

        # Vectorized for CKKS
        encrypted = ts.ckks_vector(self.context, [float(x) for x in list(data.values())])
        ciphertext_b64 = base64.b64encode(encrypted.serialize()).decode()

        await self.supabase.record_event("he_encrypted", {"job_id": job_id, "type": "ckks_vector"})

        return EncryptedPayload(
            ciphertext=ciphertext_b64,
            context=base64.b64encode(self.context.serialize()).decode(),
            metadata={"scheme": "ckks"},
        )

    async def decrypt(self, payload: dict[str, Any]) -> dict[str, Any]:
        encrypted = payload["encrypted"]
        job_id = payload["job_id"]

        if not self.enabled or encrypted.context == "plaintext":
            return eval(base64.b64decode(encrypted.ciphertext).decode())

        ctx_bytes = base64.b64decode(encrypted.context)
        ct_bytes = base64.b64decode(encrypted.ciphertext)

        context = ts.context_from(ctx_bytes)
        vector = ts.lazy_ckks_vector_from(context, ct_bytes)
        decrypted = vector.decrypt()

        await self.supabase.record_event("he_decrypted", {"job_id": job_id})
        return {"decrypted": decrypted}

    async def homomorphic_aggregate(self, payload: dict[str, Any]) -> EncryptedPayload:
        encrypted_updates: list[EncryptedPayload] = payload["updates"]
        if not self.enabled:
            return encrypted_updates[0]

        result = None
        for upd in encrypted_updates:
            vec = ts.lazy_ckks_vector_from(self.context, base64.b64decode(upd.ciphertext))
            if result is None:
                result = vec
            else:
                result += vec

        serialized = result.serialize()
        return EncryptedPayload(
            ciphertext=base64.b64encode(serialized).decode(),
            context=base64.b64encode(self.context.serialize()).decode(),
            metadata={"aggregated": True},
        )
