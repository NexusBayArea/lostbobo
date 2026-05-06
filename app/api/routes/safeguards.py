from fastapi import APIRouter
from app.kernel.kernel import Kernel

router = APIRouter(prefix="/safeguards", tags=["safeguards"])

kernel = Kernel()


@router.post("/gate")
async def gate_action(action: dict):
    return await kernel.execute({"type": "SAFEGUARD_GATE", "payload": action})


@router.post("/monitor")
async def monitor(payload: dict):
    return await kernel.execute({"type": "MONITOR_METRIC", "payload": payload})