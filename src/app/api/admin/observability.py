from fastapi import APIRouter
from pathlib import Path
import json

router = APIRouter()

TRACE_FILE = Path(__file__).resolve().parents[5] / "runtime_trace.json"


@router.get("/admin/observability")
def get_trace():
    if not TRACE_FILE.exists():
        return {"status": "no data"}

    return json.loads(TRACE_FILE.read_text())
