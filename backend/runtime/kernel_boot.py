"""
Kernel boot module — entry point for the SimHPC kernel runtime.
Wires all subsystems, registers built-in capabilities, and starts background dispatchers.
"""

from __future__ import annotations

import logging

from backend.core.auth.policy_engine import get_policy_engine
from backend.core.health import HealthProbe
from backend.core.protocol.bus.protocol_bus import KernelProtocolBus
from backend.core.protocol.contracts.plugin_message_protocol import PluginMessageProtocol
from backend.core.runtime_manifest import RuntimeManifest
from backend.core.trust.behavioral_engine import BehavioralTrustEvaluator
from backend.core.trust.capability_advertisement import CapabilityAdvertisementManager
from backend.core.trust.handshake import A2AHandshakeProtocol, SessionManager
from backend.core.trust.identity import IdentityVerifier, TrustStore
from backend.core.trust.message_contracts import MessageContractEnforcer
from backend.core.trust.plugin_verification import PluginVerificationPipeline
from backend.core.trust.telemetry_hook import TrustTelemetry
from backend.core.trust.trust_decay import TrustDecayEngine
from backend.core.trust.trust_graph import TrustGraphAnalyzer
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

    # --- Trust Subsystem ---
    kernel.trust_store = TrustStore()
    kernel.identity_verifier = IdentityVerifier()
    kernel.session_manager = SessionManager()
    kernel.trust_telemetry = TrustTelemetry()
    kernel.trust_evaluator = BehavioralTrustEvaluator(
        anomaly_detector=kernel.anomaly_detector,
        event_log=kernel.event_store,
        telemetry=kernel.trust_telemetry,
    )
    kernel.trust_graph = TrustGraphAnalyzer()
    kernel.trust_decay = TrustDecayEngine()

    log.info("Trust subsystem initialized (behavioral engine + trust graph + decay)")

    # --- A2A Handshake Protocol ---
    kernel.handshake_protocol = A2AHandshakeProtocol(kernel)
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

    # --- Trust Capabilities ---
    kernel.capabilities.register(
        "trust.verify_plugin",
        PluginVerificationPipeline(kernel).verify,
    )

    cap_ad_mgr = CapabilityAdvertisementManager(kernel.capabilities)
    kernel.capabilities.register(
        "trust.advertise_capability",
        cap_ad_mgr.advertise,
    )

    # --- Message Contract Enforcement Middleware ---
    kernel.protocol_bus.add_middleware(MessageContractEnforcer(cap_ad_mgr))

    # --- Policy Engine (trust-aware) ---
    kernel.policy_engine = get_policy_engine()

    # --- Built-in Capabilities ---
    from backend.core.memory.capabilities.rag_capabilities import register_rag_capabilities

    await register_rag_capabilities(kernel)
    log.info("RAG capabilities registered (retrieve, rerank, compress, graphrag, streaming_rag)")

    from backend.core.document.capabilities import register_document_capabilities

    await register_document_capabilities(kernel)
    log.info("Document capabilities registered (generate_pdf, generate_certificate, ingest_pdf)")

    _register_observability_capabilities(kernel)
    log.info("Observability capabilities registered (dag_state, list_executions)")

    await _register_memory_recall(kernel)
    log.info("Memory recall capability registered")

    log.info("Built-in capabilities registered")


def _register_observability_capabilities(kernel):
    async def dag_state(payload: dict) -> dict:
        dag_id = payload.get("dag_id", "")
        rec = await kernel.memory_fabric.retrieve_by_id(dag_id)
        if rec is None:
            return {"nodes": [], "edges": []}
        dag_nodes = getattr(rec, "dag_nodes", []) or []
        dag_edges = getattr(rec, "dag_edges", []) or []
        return {
            "nodes": [
                {
                    "id": n.node_id if hasattr(n, "node_id") else str(i),
                    "label": getattr(n, "capability", ""),
                    "status": getattr(n, "state", "unknown"),
                }
                for i, n in enumerate(dag_nodes)
            ],
            "edges": [
                {"source": e.source if hasattr(e, "source") else "", "target": e.target if hasattr(e, "target") else ""}
                for e in dag_edges
            ],
        }

    async def list_executions(payload: dict) -> dict:
        tenant_id = payload.get("tenant_id", "default")
        records = await kernel.memory_fabric.retrieve_by_type(tenant_id=tenant_id, memory_type="execution")
        return {
            "executions": [
                {
                    "id": r.memory_id,
                    "plugin": r.plugin_name,
                    "timestamp": r.timestamp,
                    "status": getattr(r, "execution_state", {}).get("status", "unknown")
                    if hasattr(r, "execution_state")
                    else "unknown",
                }
                for r in records
            ]
        }

    kernel.capabilities.register("observability.dag_state", dag_state)
    kernel.capabilities.register("observability.list_executions", list_executions)


async def _register_memory_recall(kernel):
    async def recall_handler(payload: dict) -> dict:
        tenant_id = payload["tenant_id"]
        mem_type = payload.get("memory_type")
        limit = payload.get("limit", 50)
        filters = payload.get("filters", {})

        records = await kernel.memory_fabric.retrieve_by_type(
            tenant_id=tenant_id, memory_type=mem_type, filter_dict=filters
        )
        return {
            "records": [r.model_dump() for r in records[:limit]],
            "total": len(records),
        }

    kernel.capabilities.register("memory.recall", recall_handler)

    log.info("Kernel boot complete")
