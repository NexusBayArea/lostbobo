from __future__ import annotations

from collections import defaultdict


class FairnessEngine:
    def __init__(self, max_gpu_per_tenant: float = 4.0):
        self.usage: dict[str, float] = defaultdict(float)
        self.max_per_tenant = max_gpu_per_tenant

    def can_schedule(self, tenant_id: str, gpu_fraction: float) -> bool:
        return (self.usage[tenant_id] + gpu_fraction) <= self.max_per_tenant

    def record_usage(self, tenant_id: str, gpu_fraction: float):
        self.usage[tenant_id] += gpu_fraction

    def release(self, tenant_id: str, gpu_fraction: float):
        self.usage[tenant_id] = max(0.0, self.usage[tenant_id] - gpu_fraction)
