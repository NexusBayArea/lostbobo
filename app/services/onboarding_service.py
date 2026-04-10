import logging
from typing import Tuple, Dict, Any
from datetime import datetime
from supabase import Client
from app.models.onboarding import OnboardingUpdate

logger = logging.getLogger(__name__)


class OnboardingService:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    def get_or_create_state(self, user_id: str) -> Dict[str, Any]:
        """Fetch current onboarding state or create a new one."""
        try:
            # Check Supabase
            response = (
                self.supabase.table("onboarding_state")
                .select("*")
                .eq("user_id", user_id)
                .single()
                .execute()
            )

            if response.data:
                return response.data

            # Create new state if not exists
            new_state = {
                "user_id": user_id,
                "current_step": "welcome",
                "completed_steps": [],
                "events": [],
                "skipped": False,
                "version": 1,
            }
            insert_resp = (
                self.supabase.table("onboarding_state").insert(new_state).execute()
            )
            if insert_resp.data:
                return insert_resp.data[0]

            return new_state

        except Exception as e:
            logger.error(f"Error fetching/creating onboarding state: {e}")
            # Fallback mock for non-DB users if needed
            return {
                "user_id": user_id,
                "current_step": "welcome",
                "completed_steps": [],
                "events": [],
                "skipped": False,
                "version": 1,
                "updated_at": datetime.utcnow().isoformat(),
            }

    def update_state(
        self, user_id: str, payload: OnboardingUpdate
    ) -> Tuple[Dict[str, Any], str]:
        """Update state with version conflict check."""
        try:
            db_state = self.get_or_create_state(user_id)

            # Version conflict check
            if payload.version < db_state.get("version", 1):
                logger.warning(
                    f"Version conflict for user {user_id}: incoming {payload.version}, db {db_state.get('version')}"
                )
                return db_state, "conflict"

            # Increment version
            new_version = db_state.get("version", 1) + 1

            update_data = {
                "current_step": payload.current_step,
                "completed_steps": payload.completed_steps,
                "events": payload.events,
                "skipped": payload.skipped,
                "version": new_version,
                "updated_at": datetime.utcnow().isoformat(),
            }

            response = (
                self.supabase.table("onboarding_state")
                .update(update_data)
                .eq("user_id", user_id)
                .execute()
            )

            if response.data:
                return response.data[0], "ok"

            return db_state, "error"

        except Exception as e:
            logger.error(f"Error updating onboarding state: {e}")
            return {}, "error"

    def add_event(self, user_id: str, event: str) -> Dict[str, Any]:
        """Track single event only."""
        try:
            db_state = self.get_or_create_state(user_id)

            events = db_state.get("events", [])
            if event not in events:
                events.append(event)

            # Increment version for events too
            new_version = db_state.get("version", 1) + 1

            update_data = {
                "events": events,
                "version": new_version,
                "updated_at": datetime.utcnow().isoformat(),
            }

            response = (
                self.supabase.table("onboarding_state")
                .update(update_data)
                .eq("user_id", user_id)
                .execute()
            )

            if response.data:
                return response.data[0]

            return db_state

        except Exception as e:
            logger.error(f"Error adding event: {e}")
            return {}
