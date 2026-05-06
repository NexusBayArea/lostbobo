from fastapi import APIRouter
from app.kernel.kernel import Kernel

router = APIRouter(prefix="/workspace", tags=["workspace"])

kernel = Kernel()


@router.post("/prompt")
async def build_prompt(payload: dict):
    return await kernel.execute({
        "type": "BUILD_PROMPT",
        "payload": payload
    })