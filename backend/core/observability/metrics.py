from opentelemetry import metrics

meter = metrics.get_meter(__name__)

kernel_commands_counter = meter.create_counter(
    name="kernel_commands_total",
    description="Total number of kernel commands dispatched",
    unit="1",
)

def increment_kernel_commands(tenant_id: str):
    kernel_commands_counter.add(1, {"tenant.id": tenant_id})
