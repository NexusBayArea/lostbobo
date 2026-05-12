from functools import wraps

from opentelemetry import trace


def trace_kernel(name: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)
            with tracer.start_as_current_span(name):
                return await func(*args, **kwargs)

        return wrapper

    return decorator
