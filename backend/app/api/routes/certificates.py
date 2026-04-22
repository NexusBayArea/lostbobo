import hashlib
import json
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel

from app.core.supabase import supabase
from app.services.pdf_service import PDFService

logger = logging.getLogger(__name__)
router = APIRouter()

# Global references populated by init_routes
_supabase = None
_redis = None
_verify_auth = None
_get_job = None
_update_job_field = None


def init_routes(supabase_client, r_client, verify_auth, get_job, update_job_field):
    """Initialize dependencies from the main app."""
    global _supabase, _redis, _verify_auth, _get_job, _update_job_field
    _supabase = supabase_client
    _redis = r_client
    _verify_auth = verify_auth
    _get_job = get_job
    _update_job_field = update_job_field


class CertificateVerifyResponse(BaseModel):
    is_valid: bool
    job_id: str
    issued_at: str
    signature_hash: str
    verified_data: dict


@router.post("/generate/{job_id}")
async def generate_certificate(job_id: str, user: Annotated[dict, Depends(lambda: _verify_auth)]):
    """Generates an immutable certificate for a completed simulation."""
    if not _supabase:
        raise HTTPException(503, "Database connection unavailable")

    user_id = user.get("user_id_internal")

    # 1. Fetch the simulation record
    res = _supabase.table("simulations").select("*").eq("job_id", job_id).eq("user_id", user_id).single().execute()
    sim_data = res.data

    if not sim_data or sim_data.get("status") != "completed":
        raise HTTPException(400, "Simulation not found or not completed.")

    # 2. Check if certificate already exists
    cert_check = _supabase.table("simulation_certificates").select("certificate_id").eq("job_id", job_id).execute()
    if cert_check.data:
        return {
            "status": "success",
            "certificate_id": cert_check.data[0]["certificate_id"],
            "message": "Certificate already exists",
        }

    # 3. Create the Cryptographic Signature
    payload_to_hash = {
        "job_id": job_id,
        "input_params": sim_data.get("input_params", {}),
        "result_summary": sim_data.get("result_summary", {}),
        "completed_at": sim_data.get("updated_at"),
    }

    hash_string = json.dumps(payload_to_hash, sort_keys=True).encode("utf-8")
    signature = hashlib.sha256(hash_string).hexdigest()

    # 4. Store the Certificate
    new_cert = (
        _supabase.table("simulation_certificates")
        .insert(
            {
                "job_id": job_id,
                "user_id": user_id,
                "signature_hash": signature,
                "metadata": {"algorithm": "sha256"},
            }
        )
        .execute()
    )

    cert_id = new_cert.data[0]["certificate_id"]

    return {
        "status": "success",
        "certificate_id": cert_id,
        "signature": signature,
        "verification_url": f"https://simhpc.com/verify/{cert_id}",
    }


@router.get("/download/{cert_hash}")
async def download_certificate(cert_hash: str):
    """
    Fetches simulation metadata and generates a verifiable PDF report.
    """
    # 1. Verify the certificate exists in our 'Moat'
    res = supabase.table("simulation_history").select("*").eq("certificate_hash", cert_hash).single().execute()

    if not res.data:
        raise HTTPException(status_code=404, detail="Certificate not found")

    # 2. Generate the PDF buffer
    pdf_service = PDFService()
    pdf_buffer = pdf_service.generate_report(res.data)

    # 3. Stream the file back to the browser
    return Response(
        content=pdf_buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=SimHPC_Report_{cert_hash[:8]}.pdf"},
    )
