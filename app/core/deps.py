from app.core.db import get_supabase_client as _get_supabase_client


def get_supabase_client():
    """Dependency for getting Supabase client"""
    return _get_supabase_client()
