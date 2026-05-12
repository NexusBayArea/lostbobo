from __future__ import annotations

from fastapi import APIRouter, Depends

router = APIRouter(prefix="/api/v1/observability", tags=["observability"])


def get_kernel(request):
    return request.app.state.kernel


def get_tenant_id(request):
    return request.headers.get("X-Tenant-ID", "default")


KernelDep = Depends(get_kernel)


@router.get("/dag/{dag_id}")
async def get_dag_state(dag_id: str, kernel=KernelDep):
    state = await kernel.capabilities.invoke("observability.dag_state", {"dag_id": dag_id})
    return state


@router.get("/simulations")
async def list_simulations(kernel=KernelDep):
    tenant_id = "default"
    return await kernel.capabilities.invoke("observability.list_executions", {"tenant_id": tenant_id})
