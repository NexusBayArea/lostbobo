from __future__ import annotations

import jsonschema

from backend.core.trust.capability_advertisement import CapabilityAdvertisementManager


class MessageContractEnforcer:
    """Validates inter-plugin messages against registered schemas.
    Added as middleware to the protocol bus."""

    def __init__(self, cap_ad_mgr: CapabilityAdvertisementManager):
        self.cap_ad_mgr = cap_ad_mgr

    async def before(self, context: dict) -> dict:
        envelope = context["envelope"]
        if envelope.protocol != "plugin_message":
            return context
        capability = envelope.payload.get("capability")
        if not capability:
            return context
        schema = self.cap_ad_mgr.get_schema(capability)
        if not schema:
            return context
        input_schema = schema.get("input_schema")
        if input_schema:
            try:
                jsonschema.validate(
                    instance=envelope.payload.get("input", {}),
                    schema=input_schema,
                )
            except jsonschema.ValidationError as e:
                raise PermissionError(f"Input validation failed for {capability}: {e.message}") from e
        return context
