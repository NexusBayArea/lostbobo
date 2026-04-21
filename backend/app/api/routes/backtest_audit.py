from fastapi import APIRouter, HTTPException
from backend.app.core.supabase import supabase

router = APIRouter()

@router.post("/api/v1/backtest/{run_id}/audit")
async def audit_backtest(run_id: str):
    res = supabase.table("walk_forward_windows") \
        .select("*") \
        .eq("run_id", run_id) \
        .execute()
    
    windows = res.data
    flags = []
    scores = []

    for w in windows:
        metrics = w.get("metrics")
        if not metrics:
            continue

        if metrics.get("sharpe", 0) > 3:
            flags.append({"type": "STATISTICAL_ANOMALY", "severity": "HIGH", "window_id": w["id"], "message": "Sharpe ratio exceeds realistic bounds"})
            scores.append(0.3)
        if metrics.get("max_drawdown", 0) >= 0:
            flags.append({"type": "EXECUTION_ANOMALY", "severity": "HIGH", "window_id": w["id"], "message": "No drawdown detected"})
            scores.append(0.3)

    audit_score = min(1.0, sum(scores))
    result = {
        "audit_score": audit_score,
        "confidence": 1.0 - audit_score,
        "flags": flags,
        "summary": "Auto-generated audit summary"
    }

    supabase.table("walk_forward_runs").update({
        "audit_result": result,
        "audit_score": audit_score
    }).eq("id", run_id).execute()

    return result
