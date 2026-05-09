from fastapi import APIRouter

from backend.core.supabase import get_supabase_client

router = APIRouter(prefix="/flywheel", tags=["flywheel"])


@router.get("/discovery/{discovery_id}/parameters")
async def get_discovery_parameters(discovery_id: str):
    db = get_supabase_client()
    result = (
        db.table("discovery_leaderboard")
        .select("*, certificates(full_certificate)")
        .eq("discovery_id", discovery_id)
        .single()
        .execute()
    )

    if not result.data:
        return {"parameters": {}}

    cert = result.data.get("certificates") or {}
    params = cert.get("full_certificate", {}).get("suggested_parameters", {})

    return {"parameters": params, "source": "certified"}
