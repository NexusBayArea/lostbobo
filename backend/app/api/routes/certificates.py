import hashlib
import json
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

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
async def generate_certificate(job_id: str, user: dict = Depends(lambda: _verify_auth)):
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
        return {"status": "success", "certificate_id": cert_check.data[0]["certificate_id"], "message": "Certificate already exists"}

    # 3. Create the Cryptographic Signature
    payload_to_hash = {
        "job_id": job_id,
        "input_params": sim_data.get("input_params", {}),
        "result_summary": sim_data.get("result_summary", {}),
        "completed_at": sim_data.get("updated_at")
    }
    
    hash_string = json.dumps(payload_to_hash, sort_keys=True).encode('utf-8')
    signature = hashlib.sha256(hash_string).hexdigest()

    # 4. Store the Certificate
    new_cert = _supabase.table("simulation_certificates").insert({
        "job_id": job_id,
        "user_id": user_id,
        "signature_hash": signature,
        "metadata": {"algorithm": "sha256"}
    }).execute()

    cert_id = new_cert.data[0]["certificate_id"]

    return {
        "status": "success",
        "certificate_id": cert_id,
        "signature": signature,
        "verification_url": f"https://simhpc.com/verify/{cert_id}"
    }

@router.get("/verify/{certificate_id}", response_model=CertificateVerifyResponse)
async def verify_certificate(certificate_id: str):
    """
    PUBLIC ENDPOINT: Allows third parties to verify a simulation result.
    Does NOT require authentication.
    """
    if not _supabase:
        raise HTTPException(503, "Database connection unavailable")

    # 1. Fetch the certificate
    cert_res = _supabase.table("simulation_certificates").select("*").eq("certificate_id", certificate_id).single().execute()
    cert_data = cert_res.data

    if not cert_data:
        raise HTTPException(404, "Invalid Certificate ID")

    # 2. Fetch the underlying simulation data
    sim_res = _supabase.table("simulations").select("input_params, result_summary, updated_at").eq("job_id", cert_data["job_id"]).single().execute()
    sim_data = sim_res.data

    if not sim_data:
        raise HTTPException(500, "Underlying simulation data missing")

    # 3. Recalculate the hash
    payload_to_hash = {
        "job_id": cert_data["job_id"],
        "input_params": sim_data.get("input_params", {}),
        "result_summary": sim_data.get("result_summary", {}),
        "completed_at": sim_data.get("updated_at")
    }
    recalculated_hash = hashlib.sha256(json.dumps(payload_to_hash, sort_keys=True).encode('utf-8')).hexdigest()

    is_valid = recalculated_hash == cert_data["signature_hash"]

    return {
        "is_valid": is_valid,
        "job_id": cert_data["job_id"],
        "issued_at": cert_data["issued_at"],
        "signature_hash": cert_data["signature_hash"],
        "verified_data": sim_data if is_valid else {"error": "Data integrity check failed. Records may have been altered."}
    }
