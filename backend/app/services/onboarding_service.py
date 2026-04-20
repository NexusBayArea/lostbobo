import logging
from typing import Dict, Any
from backend.app.core.supabase import supabase

logger = logging.getLogger(__name__)

class OnboardingService:
    def __init__(self):
        self.INITIAL_GIFT = 10  # Give 10 credits on signup

    async def onboard_new_user(self, user_id: str) -> Dict[str, Any]:
        """Provisions a new user with their initial credits and profile setup."""
        try:
            # 1. Check if already onboarded
            res = supabase.table("profiles").select("last_onboarded_at").eq("id", user_id).single().execute()
            
            if res.data and res.data.get("last_onboarded_at"):
                return {"status": "existing", "message": "User already onboarded."}

            # 2. Grant initial credits
            supabase.table("profiles").update({
                "credit_balance": self.INITIAL_GIFT,
                "last_onboarded_at": "now()"
            }).eq("id", user_id).execute()

            # 3. Log to Ledger
            supabase.table("credit_ledger").insert({
                "user_id": user_id,
                "amount": self.INITIAL_GIFT,
                "reason": "signup_bonus"
            }).execute()

            logger.info(f"User {user_id} onboarded with {self.INITIAL_GIFT} credits.")
            return {"status": "success", "credits_granted": self.INITIAL_GIFT}

        except Exception as e:
            logger.error(f"Onboarding failed for {user_id}: {str(e)}")
            raise e

onboarding_service = OnboardingService()
