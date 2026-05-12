"""Minimal OpenTelemetry tracing context manager used across the kernel."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any

from opentelemetry import trace


@contextmanager
def trace_context(name: str, attributes: dict[str, Any] | None = None):
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span(name) as span:
        if attributes:
            span.set_attributes(attributes)
        yield span
