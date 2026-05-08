import asyncio
import os
from typing import Any

from opentelemetry import logs, metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource

from backend.core.supabase_job_store import SupabaseJobStore
from backend.kernel.kernel import Kernel


class ObservabilityService:
    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.supabase = SupabaseJobStore()

        resource = Resource.create({"service.name": "simhpc"})

        # Logging (Loki via OTLP)
        logger_provider = LoggerProvider(resource=resource)
        logs.set_logger_provider(logger_provider)

        log_exporter = OTLPLogExporter(
            endpoint=os.getenv("OTEL_EXPORTER_OTLP_LOGS_ENDPOINT", "http://loki:3100/otlp/v1/logs")
        )
        logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))

        self.logger = logs.get_logger(__name__)
        self.tracer = trace.get_tracer(__name__)
        self.meter = metrics.get_meter(__name__)

    def emit_log(self, level: str, message: str, attributes: dict[str, Any] = None):
        """Emit structured log to Loki + Supabase."""
        attributes = attributes or {}
        attributes.update(
            {
                "service.name": "simhpc",
                "simhpc.job_id": getattr(self.kernel, "current_job_id", ""),
                "simhpc.tenant_id": attributes.get("tenant_id", "unknown"),
            }
        )

        self.logger.emit(level=level, body=message, attributes=attributes)

        # Also persist critical logs to Supabase
        if level in ["ERROR", "WARNING", "CRITICAL"]:
            asyncio.create_task(
                self.supabase.record_event(
                    "structured_log", {"level": level, "message": message, "attributes": attributes}
                )
            )
