import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
from backend.core.kernel.kernel import Kernel
from backend.core.supabase_job_store import SupabaseJobStore

class TracingService:
    """Kernel-centered OpenTelemetry tracing service."""

    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.supabase = SupabaseJobStore()

        resource = Resource.create({
            ResourceAttributes.SERVICE_NAME: "simhpc",
            ResourceAttributes.SERVICE_VERSION: "0.4.0",
            ResourceAttributes.DEPLOYMENT_ENVIRONMENT: os.getenv("ENV", "production"),
        })

        provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(provider)

        # Jaeger via OTLP (recommended path)
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://jaeger:4317")
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)

        provider.add_span_processor(BatchSpanProcessor(exporter))

        self.tracer = trace.get_tracer(__name__)

    def start_span(self, name: str, attributes: dict = None):
        """Create traceable span through Kernel"""
        span = self.tracer.start_span(
            name,
            attributes={
                **(attributes or {}),
                "simhpc.kernel": "true",
                "simhpc.supabase_job_id": attributes.get("job_id", "") if attributes else "",
            },
        )
        return span

    async def trace_command(self, command_name: str, payload: dict):
        """Trace any Kernel command execution"""
        with self.start_span(
            f"command.{command_name}",
            {
                "command": command_name,
                "tenant_id": payload.get("tenant_id"),
                "job_id": payload.get("job_id"),
            },
        ) as span:
            try:
                result = await self.kernel.command_bus.execute(command_name, payload)
                span.set_attribute("status", "success")
                return result
            except Exception as e:
                span.set_attribute("status", "error")
                span.record_exception(e)
                raise
