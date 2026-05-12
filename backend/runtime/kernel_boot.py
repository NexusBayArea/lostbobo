"""
Kernel boot module — entry point for the SimHPC kernel runtime.
Wires all subsystems, registers built-in capabilities, and starts background dispatchers.
"""

from __future__ import annotations

import logging

from backend.core.health import HealthProbe
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

    kernel.handshake_protocol = HandshakeProtocol(
        trust_store=kernel.trust_store,
        identity_verifier=kernel.identity_verifier,
        session_manager=kernel.session_manager,
    )

    log.info("Handshake protocol ready")

    log.info("Built-in capabilities registered")

    log.info("Kernel boot complete")
