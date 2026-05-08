import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from backend.core.kernel.command_bus import command_bus


class PrometheusMetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start

        await command_bus.execute(
            "RECORD_METRICS",
            {
                "method": request.method,
                "route": request.url.path,
                "status": response.status_code,
                "duration": duration,
                "tenant_id": request.headers.get("X-Tenant-ID", "unknown"),
            },
        )
        return response
