import hashlib
import json
from datetime import timedelta
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends

from app.api.schemas.backtest import BacktestCreate
from app.core.supabase import supabase
from app.gateway import verify_auth

router = APIRouter()


def enqueue_simulation(job_data: dict):
    # Dummy enqueue logic for demonstration
    pass


@router.post("/api/v1/backtest/run")
async def create_backtest(payload: BacktestCreate, user: Annotated[dict, Depends(verify_auth)]):
    run_id = str(uuid4())

    supabase.table("walk_forward_runs").insert(
        {
            "id": run_id,
            "org_id": user.get("org_id", str(uuid4())),
            "strategy_id": payload.strategy_id,
            "dataset_id": payload.dataset_id,
            "status": "queued",
        }
    ).execute()

    cursor = payload.start_date
    while cursor + timedelta(days=payload.train_window_days + payload.test_window_days) <= payload.end_date:
        train_start = cursor
        train_end = cursor + timedelta(days=payload.train_window_days)
        test_start = train_end
        test_end = train_end + timedelta(days=payload.test_window_days)

        contract = {
            "strategy_id": payload.strategy_id,
            "dataset_id": payload.dataset_id,
            "train_start": str(train_start),
            "train_end": str(train_end),
            "test_start": str(test_start),
            "test_end": str(test_end),
        }

        contract_hash = hashlib.sha256(json.dumps(contract, sort_keys=True).encode()).hexdigest()
        window_id = str(uuid4())

        supabase.table("walk_forward_windows").insert(
            {
                "id": window_id,
                "run_id": run_id,
                "train_start": str(train_start),
                "train_end": str(train_end),
                "test_start": str(test_start),
                "test_end": str(test_end),
                "contract_hash": contract_hash,
                "status": "queued",
            }
        ).execute()

        enqueue_simulation({"type": "backtest_window", "window_id": window_id, "contract": contract})

        cursor += timedelta(days=payload.step_days)

    return {"run_id": run_id, "status": "queued"}
