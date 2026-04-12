import hashlib
import json
import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException

router = APIRouter()
logger = logging.getLogger(__name__)


def verify_auth(authorization: str = Header(None)) -> dict:
    """Stub replaced by init_routes()."""
    raise RuntimeError("verify_auth not initialized — call init_routes() first")


supabase_client: Any = None
r_client: Any = None
get_job: Any = None
update_job_field: Any = None


def init_routes(supabase, redis, auth_dep, get_j, update_jf):
    global supabase_client, r_client, verify_auth, get_job, update_job_field
    supabase_client = supabase
    r_client = redis
    verify_auth = auth_dep
    get_job = get_j
    update_job_field = update_jf


@router.post("/simulations/{sim_id}/certificate", tags=["Certificates"])
async def generate_certificate(
    sim_id: str,
    idempotency_key: str = Header(None, alias="Idempotency-Key"),
    user: dict = Depends(verify_auth),
):
    """Generate a Physics Validation Certificate."""
    job = get_job(sim_id)
    if not job:
        raise HTTPException(404, "Simulation not found")
    if job.get("status") != "completed":
        raise HTTPException(409, "Simulation not completed")

    existing = job.get("certificate_id")
    if existing:
        return {
            "simulation_id": sim_id,
            "certificate_id": existing,
            "status": "generated",
            "download_url": job.get("pdf_url") or "",
            "verification_url": f"https://simhpc.com/verify/{existing}",
        }

    audit_result = job.get("audit_result", {})
    verification_hash = hashlib.sha256(
        json.dumps(audit_result, sort_keys=True).encode()
    ).hexdigest()

    cert_id = f"cert_{uuid.uuid4().hex[:8]}"
    pdf_url = job.get("pdf_url") or ""

    if supabase_client:
        try:
            supabase_client.table("certificates").insert(
                {
                    "id": cert_id,
                    "simulation_id": sim_id,
                    "verification_hash": verification_hash,
                    "storage_url": pdf_url,
                }
            ).execute()
            supabase_client.table("simulations").update(
                {
                    "certificate_id": cert_id,
                }
            ).eq("job_id", sim_id).execute()
        except Exception as e:
            logger.error(f"Certificate creation failed: {e}")

    update_job_field(sim_id, "certificate_id", cert_id)

    return {
        "simulation_id": sim_id,
        "certificate_id": cert_id,
        "status": "generated",
        "download_url": pdf_url,
        "verification_url": f"https://simhpc.com/verify/{cert_id}",
    }


@router.get("/certificates/{cert_id}/verify", tags=["Certificates"])
async def verify_certificate(cert_id: str):
    """Verify a certificate via QR code scan."""
    if not supabase_client:
        raise HTTPException(503, "Verification service unavailable")

    try:
        result = (
            supabase_client.table("certificate_verification_view")
            .select("*")
            .eq("certificate_id", cert_id)
            .single()
            .execute()
        )

        if not result.data:
            return {"verified": False, "message": "Certificate not found"}

        data = result.data
        return {
            "verified": True,
            "certificate_id": data["certificate_id"],
            "simulation_id": str(data["simulation_id"]),
            "verification_hash": data["verification_hash"],
            "timestamp": data["created_at"],
            "hallucination_score": data.get("hallucination_score"),
            "audit_status": data.get("audit_result", {}).get("status", "unknown"),
            "summary": data.get("audit_result", {}).get("summary", {}),
        }
    except Exception as e:
        logger.error(f"Certificate verification failed: {e}")
        return {"verified": False, "message": str(e)}
