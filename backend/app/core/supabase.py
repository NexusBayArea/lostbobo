from supabase import Client, create_client

from app.core.config import settings


def get_supabase() -> Client:
    return create_client(settings.SB_URL, settings.SB_SECRET_KEY)


supabase = get_supabase()
