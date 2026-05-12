from __future__ import annotations

from typing import Any

from backend.core.sdk.registries.capability_registry import CapabilityRegistry


class CapabilityAdvertisementManager:
    """Handles capability advertisement and schema registration.
    Registered as capability 'trust.advertise_capability'."""

    def __init__(self, registry: CapabilityRegistry):
        self.registry = registry
        self._schemas: dict[str, dict[str, Any]] = {}

    async def advertise(self, payload: dict) -> dict:
        plugin_id = payload["plugin_id"]
        caps = payload["capabilities"]
        for cap in caps:
            cap_name = cap["name"]
            self.registry.register(cap_name, None, plugin_id)
            self._schemas[cap_name] = {
                "input_schema": cap.get("input_schema"),
                "output_schema": cap.get("output_schema"),
                "version": cap.get("version", "1.0"),
                "requires_trust_score": cap.get("requires_trust_score", 0.0),
                "max_requests_per_minute": cap.get("max_requests_per_minute", 100),
            }
        return {"advertised": len(caps)}

    def get_schema(self, capability_name: str) -> dict | None:
        return self._schemas.get(capability_name)
