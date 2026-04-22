from app.core.supabase import supabase


class OnboardingService:
    @staticmethod
    async def provision_new_user(user_id: str):
        """
        Calls the RPC function to safely grant 10 credits.
        Returns the updated status for the UI.
        """
        try:
            # Execute the Postgres function
            supabase.rpc("gift_signup_bonus", {"target_user_id": user_id}).execute()

            # Fetch updated balance to confirm
            res = supabase.table("profiles").select("credit_balance").eq("id", user_id).single().execute()
            return {"status": "success", "new_balance": res.data["credit_balance"]}
        except Exception as e:
            return {"status": "error", "message": str(e)}


onboarding_service = OnboardingService()
