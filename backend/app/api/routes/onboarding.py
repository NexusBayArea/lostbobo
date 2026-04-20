from fastapi import APIRouter, HTTPException, Depends
from backend.app.services.onboarding_service import onboarding_service
from backend.app.core.supabase import supabase

router = APIRouter()

@router.post("/initialize")
async def initialize_user(user_id: str):
    try:
        result = await onboarding_service.onboard_new_user(user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
