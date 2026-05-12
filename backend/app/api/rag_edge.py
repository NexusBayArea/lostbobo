from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, Request
from sse_starlette.sse import EventSourceResponse

router = APIRouter(prefix="/api/v1/rag", tags=["RAG"])


def get_kernel(request):
    return request.app.state.kernel


KernelDep = Depends(get_kernel)


def get_tenant_id(request: Request) -> str:
    return request.headers.get("X-Tenant-ID", "default")


@router.get("/stream")
async def rag_stream(query: str, request: Request, kernel=KernelDep):
    tenant_id = get_tenant_id(request)
    execution_id = str(uuid.uuid4())

    async def event_generator():
        async for event in await kernel.capabilities.invoke(
            "memory.streaming_rag",
            {"query": query, "tenant_id": tenant_id, "execution_id": execution_id},
        ):
            yield {"data": json.dumps(event)}

    return EventSourceResponse(event_generator())
