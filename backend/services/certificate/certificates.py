from fastapi import APIRouter

from backend.core.kernel.command_bus import command_bus

router = APIRouter(prefix="/certificates", tags=["certificates"])
wellknown_router = APIRouter()


@router.post("/issue")
async def issue_certificate(payload: dict):
    return await command_bus.execute("CERTIFICATE_ISSUE", payload)


@router.post("/verify")
async def verify_certificate(payload: dict):
    return await command_bus.execute("CERTIFICATE_VERIFY", payload)


@wellknown_router.get("/.well-known/simhpc-public-key.pem")
async def get_public_key():
    return {"key": "..."}
