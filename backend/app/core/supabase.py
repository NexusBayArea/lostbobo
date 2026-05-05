from supabase import Client, create_client

from backend.app.core.config import settings


def get_supabase() -> Client | None:
    if not settings.SB_URL or not settings.SB_SECRET_KEY:
        return None
    try:
        return create_client(settings.SB_URL, settings.SB_SECRET_KEY)
    except Exception:
        return None


def get_supabase_client() -> Client | None:
    return get_supabase()


supabase = get_supabase()
