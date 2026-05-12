import os

from fastapi import FastAPI
from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader


def init_observability(app: FastAPI):
    # Tracing
    FastAPIInstrumentor.instrument_app(app)

    # Metrics
    otlp_exporter = OTLPMetricExporter(endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"))
    metric_reader = PeriodicExportingMetricReader(otlp_exporter)
    provider = MeterProvider(metric_readers=[metric_reader])
    metrics.set_meter_provider(provider)
