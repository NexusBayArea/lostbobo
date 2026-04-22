from supabase import create_client

from backend.app.core.config import settings

supabase = create_client(settings.SB_URL, settings.SB_SECRET_KEY)

CURRENT_RUN_ID = None


def start_run(label="manual"):
    global CURRENT_RUN_ID
    res = supabase.table("runs").insert({"label": label}).execute()
    CURRENT_RUN_ID = res.data[0]["id"]
    return CURRENT_RUN_ID


def record(node_id, contract, deps, result, context):
    if not CURRENT_RUN_ID:
        raise RuntimeError("No active run found. Call start_run() first.")

    supabase.table("node_traces").insert(
        {
            "run_id": CURRENT_RUN_ID,
            "node_id": node_id,
            "contract": contract,
            "deps": deps,
            "result": result,
        }
    ).execute()


def load_run(run_id):
    res = supabase.table("node_traces").select("*").eq("run_id", run_id).execute()
    return res.data
