import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.semconv.resource import ResourceAttributes

from backend.core.kernel.kernel import Kernel
from backend.core.supabase_job_store import SupabaseJobStore


class TracingService:
    """Kernel-centered OpenTelemetry tracing service."""

    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.supabase = SupabaseJobStore()

        resource = Resource.create(
            {
                ResourceAttributes.SERVICE_NAME: "simhpc",
                ResourceAttributes.SERVICE_VERSION: "0.4.0",
                ResourceAttributes.DEPLOYMENT_ENVIRONMENT: os.getenv("ENV", "production"),
            }
        )

        provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(provider)

        # OTLP exporter (Jaeger, Tempo, or any OTLP backend)
        exporter = OTLPSpanExporter(
            endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://tempo:4317"), insecure=True
        )
        provider.add_span_processor(BatchSpanProcessor(exporter))

        self.tracer = trace.get_tracer(__name__)

    def start_span(self, name: str, attributes: dict = None, parent=None):
        """Create traceable span through Kernel"""
        span = self.tracer.start_span(name, attributes=attributes or {}, context=parent)
        # Link to Supabase job if available
        if "job_id" in (attributes or {}):
            span.set_attribute("simhpc.job_id", attributes["job_id"])
        return span

    async def trace_command(self, command_name: str, payload: dict):
        """Trace any Kernel command execution"""
        with self.start_span(
            f"command.{command_name}",
            {"command": command_name, "tenant_id": payload.get("tenant_id"), "job_id": payload.get("job_id")},
        ) as span:
            try:
                result = await self.kernel.command_bus.execute(command_name, payload)
                span.set_attribute("status", "success")
                return result
            except Exception as e:
                span.set_attribute("status", "error")
                span.record_exception(e)
                raise
