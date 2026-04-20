from datetime import datetime
from backend.app.core.config import settings
from supabase import create_client

supabase = create_client(settings.SB_URL, settings.SB_SECRET_KEY)

def update_job_status(job_id, status, progress=None, metrics=None):
    """Update the database so the UI reflects real-time physics progress."""
    data = {"status": status}
    if progress is not None:
        data["progress"] = progress
    if metrics:
        data.update(metrics)
    if status == "processing" and progress == 0:
        data["started_at"] = datetime.utcnow().isoformat()
    if status == "completed":
        data["completed_at"] = datetime.utcnow().isoformat()

    supabase.table("simulation_history").update(data).eq("job_id", job_id).execute()
