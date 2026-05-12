from __future__ import annotations

from typing import Any
from uuid import uuid4

from backend.core.protocol.bus.protocol_context import ProtocolContext
from backend.core.protocol.bus.protocol_envelope import ProtocolEnvelope
from backend.core.protocol.bus.protocol_response import ProtocolResponse


class KernelProtocolBus:
    def __init__(self, registry, kernel_services: dict[str, Any]):
        self.router = ProtocolRouter(registry, kernel_services)
        self.middleware: list = []

    def add_middleware(self, middleware):
        self.middleware.append(middleware)

    async def dispatch(self, envelope: ProtocolEnvelope) -> ProtocolResponse:
        context = ProtocolContext(
            tenant_id=envelope.tenant_id,
            trace_id=envelope.trace_id or str(uuid4()),
            replay_id=envelope.metadata.get("replay_id"),
            dag_id=envelope.dag_id,
            node_id=envelope.node_id,
            plugin_name=envelope.source,
        )
        ctx = {"context": context, "envelope": envelope}
        for mw in self.middleware:
            if hasattr(mw, "before"):
                ctx = await mw.before(ctx)

        response = await self.router.route(ctx["envelope"])

        ctx["response"] = response
        for mw in reversed(self.middleware):
            if hasattr(mw, "after"):
                ctx = await mw.after(ctx)
        return ctx["response"]


class ProtocolRouter:
    def __init__(self, registry, kernel_services: dict[str, Any]):
        self.registry = registry
        self.target_handlers = kernel_services

    async def route(self, envelope: ProtocolEnvelope) -> ProtocolResponse:
        protocol_handler = self.registry.get(envelope.protocol)
        if protocol_handler is None:
            raise ValueError(f"Unknown protocol: {envelope.protocol}")

        # Inject kernel services into handler instance if it has a hook
        protocol_handler._kernel_services = self.target_handlers
        return await protocol_handler.handle(envelope)
