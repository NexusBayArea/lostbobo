from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class OpenTelemetryMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        tracing = request.app.state.kernel.services["tracing"]

        with tracing.start_span(
            f"http.{request.method}.{request.url.path}",
            {
                "http.method": request.method,
                "http.route": request.url.path,
                "http.client_ip": request.client.host,
                "tenant_id": request.headers.get("X-Tenant-ID"),
            },
        ) as span:
            response = await call_next(request)
            span.set_attribute("http.status_code", response.status_code)
            return response
