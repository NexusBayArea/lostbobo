"""
OpenTelemetry Tracing + Grafana Tempo Integration
"""

import os
from typing import Any

try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.trace import get_tracer

    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False


def setup_tempo_tracing(service_name: str = "simhpc") -> Any:
    """Initialize OpenTelemetry with Grafana Tempo OTLP exporter."""
    if not OTEL_AVAILABLE:
        return _NoOpTracer()

    resource = Resource(
        attributes={
            SERVICE_NAME: service_name,
            "environment": os.getenv("ENVIRONMENT", "production"),
            "deployment": os.getenv("DEPLOYMENT", "unknown"),
        }
    )

    tempo_endpoint = os.getenv("TEMPO_OTLP_ENDPOINT", "http://tempo:4317")

    try:
        exporter = OTLPSpanExporter(
            endpoint=tempo_endpoint,
            insecure=True,
        )
        trace.set_tracer_provider(TracerProvider(resource=resource))
        trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(exporter))
        print(f"Tracing initialized → {tempo_endpoint}")
    except Exception:
        pass

    return get_tracer(__name__)


class _NoOpTracer:
    """Fallback when opentelemetry is not installed."""

    def start_as_current_span(self, name: str, attributes=None):
        return _NoOpSpan()


class _NoOpSpan:
    """Fallback span."""

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


tracer = setup_tempo_tracing("simhpc")
