from fastapi import APIRouter, Response
from prometheus_client import generate_latest

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/metrics")
async def prometheus_metrics():
    """Prometheus exposition format."""
    return Response(generate_latest(), media_type="text/plain; version=0.0.4; charset=utf-8")
