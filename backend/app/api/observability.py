import json
from pathlib import Path

from fastapi import APIRouter

router = APIRouter(prefix="/observability", tags=["observability"])

TRACE_PATH = Path("trace_latest.json")
HISTORY_PATH = Path("ci_history")


@router.get("/latest")
def get_latest_trace():
    if not TRACE_PATH.exists():
        return {"error": "no trace found"}

    return json.loads(TRACE_PATH.read_text())


@router.get("/history")
def get_history():
    if not HISTORY_PATH.exists():
        return []

    runs = []
    for f in sorted(HISTORY_PATH.glob("*.json")):
        runs.append({"name": f.name, "path": str(f)})
    return runs


@router.get("/history/{run_name}")
def get_run(run_name: str):
    path = HISTORY_PATH / run_name
    if not path.exists():
        return {"error": "not found"}

    return json.loads(path.read_text())
