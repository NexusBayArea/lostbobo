from pydantic import BaseModel
from typing import Optional, List
from datetime import date

class BacktestCreate(BaseModel):
    strategy_id: str
    dataset_id: str
    start_date: date
    end_date: date
    train_window_days: int
    test_window_days: int
    step_days: int

class BacktestRunResponse(BaseModel):
    run_id: str
    status: str

class WindowStatus(BaseModel):
    window_id: str
    simulation_id: Optional[str]
    status: str
    metrics: Optional[dict]

class BacktestStatusResponse(BaseModel):
    run_id: str
    status: str
    windows: List[WindowStatus]
