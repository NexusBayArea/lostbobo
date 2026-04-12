import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException

from app.models.onboarding import (
    EventRequest,
    OnboardingResponse,
    OnboardingUpdate,
)
from app.services.onboarding_service import OnboardingService

logger = logging.getLogger(__name__)

# Note: We'll need a way to get the supabase_client from the main app.
# Since we are creating this as a separate module, we might want to use a dependency.
# However, to keep it simple and consistent with api.py, we'll assume it's passed or available.


# Re-using the logic from api.py for dependency injection.
# In a real refactor, we'd put this in api/deps.py
async def get_current_user_id(authorization: str = Header(None)) -> str:
    """Extract user_id from Supabase JWT."""
    if not authorization:
        # Fallback for dev if needed, but in production we want this.
        # For now, let's keep it strict.
        raise HTTPException(status_code=401, detail="Missing auth token")

    # We'll import verify_user from api/auth_utils if possible,
    # or just assume it's provided.
    from app.core.auth_utils import verify_user

    try:
        payload = verify_user(authorization)
        return payload.get("sub")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")


router = APIRouter()

# This will be set by the main app during inclusion
_onboarding_service: Optional[OnboardingService] = None


def get_onboarding_service() -> OnboardingService:
    if not _onboarding_service:
        raise HTTPException(
            status_code=500, detail="Onboarding service not initialized"
        )
    return _onboarding_service


@router.get("/", response_model=OnboardingResponse)
async def get_onboarding(
    user_id: str = Depends(get_current_user_id),
    service: OnboardingService = Depends(get_onboarding_service),
):
    """Retrieve current onboarding state."""
    state = service.get_or_create_state(user_id)
    return state


@router.post("/", response_model=OnboardingResponse)
async def update_onboarding(
    payload: OnboardingUpdate,
    user_id: str = Depends(get_current_user_id),
    service: OnboardingService = Depends(get_onboarding_service),
):
    """Update onboarding state with version check."""
    state, status = service.update_state(user_id, payload)

    if status == "conflict":
        # Return 409 Conflict with latest DB state
        raise HTTPException(status_code=409, detail=state)

    if status == "error":
        raise HTTPException(status_code=500, detail="Failed to update onboarding state")

    return state


@router.post("/event", response_model=OnboardingResponse)
async def track_event(
    payload: EventRequest,
    user_id: str = Depends(get_current_user_id),
    service: OnboardingService = Depends(get_onboarding_service),
):
    """Track a single onboarding event."""
    state = service.add_event(user_id, payload.event)
    return state
