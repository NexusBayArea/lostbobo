from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/capability", tags=["capability"])


class CapabilityRequest(BaseModel):
    capability: str
    payload: dict = {}


class CapabilityResponse(BaseModel):
    success: bool
    result: dict | None = None
    error: str | None = None


def get_kernel(request):
    return request.app.state.kernel


KernelDep = Depends(get_kernel)


@router.post("/invoke", response_model=CapabilityResponse)
async def invoke_capability(req: CapabilityRequest, kernel=KernelDep):
    try:
        result = await kernel.capabilities.invoke(req.capability, req.payload)
        return CapabilityResponse(success=True, result=result)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except Exception as e:
        return CapabilityResponse(success=False, error=str(e))
