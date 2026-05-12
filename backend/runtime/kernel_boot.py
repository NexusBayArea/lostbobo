"""
Kernel boot module — entry point for the SimHPC kernel runtime.
Wires all subsystems, registers built-in capabilities, and starts background dispatchers.
"""

from __future__ import annotations

import logging

from backend.core.health import HealthProbe
from backend.core.protocol.bus.protocol_bus import KernelProtocolBus
from backend.core.protocol.contracts.plugin_message_protocol import PluginMessageProtocol
from backend.core.runtime_manifest import RuntimeManifest
from backend.core.trust.handshake import HandshakeProtocol, SessionManager
from backend.core.trust.identity import IdentityVerifier, TrustStore
from backend.core.trust.telemetry_hook import TrustTelemetry
from backend.core.workers.registration import WorkerCapabilities, register_worker

log = logging.getLogger("simhpc.kernel_boot")


async def boot(kernel) -> None:
    log.info("=== SimHPC Kernel Boot ===")

    manifest = RuntimeManifest.from_env()
    log.info("Runtime manifest: %s", manifest.model_dump())

    kernel.manifest = manifest

    kernel.health_probe = HealthProbe(kernel)
    kernel.capabilities.register(
        "health.status",
        lambda p: kernel.health_probe.status(),
    )

    kernel.capabilities.register(
        "worker.register",
        lambda p: register_worker(kernel, WorkerCapabilities(**p)),
    )

    kernel.capabilities.register(
        "runtime.manifest",
        lambda p: manifest.model_dump(),
    )

    kernel.trust_store = TrustStore()
    kernel.identity_verifier = IdentityVerifier()
    kernel.session_manager = SessionManager()
    kernel.trust_telemetry = TrustTelemetry()

    log.info("Trust subsystem initialized")

    kernel.handshake_protocol = HandshakeProtocol(kernel)
    kernel.plugin_message_protocol = PluginMessageProtocol(kernel)

    protocol_registry: dict[str, object] = {
        "a2a_handshake": kernel.handshake_protocol,
        "plugin_message": kernel.plugin_message_protocol,
    }

    kernel.protocol_bus = KernelProtocolBus(
        registry=protocol_registry,
        kernel_services={
            "simulation_executor": getattr(kernel, "simulation_executor", None),
        },
    )

    log.info("Protocol bus initialized with a2a_handshake and plugin_message protocols")

    log.info("Built-in capabilities registered")

    log.info("Kernel boot complete")
