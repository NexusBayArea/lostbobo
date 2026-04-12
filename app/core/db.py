from app.core.config import get_settings

settings = get_settings()
from supabase import Client, create_client


def get_supabase_client() -> Client:
    """
    Get Supabase client instance using normalized application settings.
    APP_URL maps to SB_URL and API_TOKEN maps to SB_TOKEN (Service Key).
    """
    return create_client(settings.APP_URL, settings.API_TOKEN)
