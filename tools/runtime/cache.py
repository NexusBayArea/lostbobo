from supabase import create_client

from backend.app.core.config import settings

supabase = create_client(settings.SB_URL, settings.SB_SECRET_KEY)


def lookup_contract(contract):
    res = supabase.table("node_traces").select("result").eq("contract", contract).limit(1).execute()

    if res.data:
        return res.data[0]["result"]

    return None
