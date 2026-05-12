from __future__ import annotations

from backend.core.trust.behavioral_engine import BehavioralTrustEvaluator
from backend.core.trust.identity import TrustVerifier
from backend.core.trust.telemetry_hook import TrustTelemetry


class PluginVerificationPipeline:
    """Registers as capability 'trust.verify_plugin'."""

    def __init__(self, kernel):
        self.kernel = kernel
        self.evaluator = BehavioralTrustEvaluator(
            kernel.event_store,
            kernel.anomaly_detector,
            kernel.memory_fabric.graph_store,
            kernel.world_fabric,
        )
        self.verifier = TrustVerifier(kernel)
        self.telemetry = TrustTelemetry(kernel.event_bus)

    async def verify(self, payload: dict) -> dict:
        plugin_id = payload["plugin_id"]
        manifest = payload["manifest"]
        plugin_bytes = payload.get("plugin_bytes")

        # 1. Static analysis
        if plugin_bytes:
            dangerous_patterns = ["os.system", "subprocess", "eval(", "exec("]
            decoded = plugin_bytes.decode("utf-8", errors="ignore")
            for pattern in dangerous_patterns:
                if pattern in decoded:
                    await self.telemetry.report(
                        "plugin_verify.rejected",
                        plugin_id,
                        {
                            "reason": f"Dangerous pattern found: {pattern}",
                        },
                    )
                    return {"approved": False, "reason": f"Dangerous pattern found: {pattern}"}

        # 2. Signature verification
        passport = manifest.get("passport", {})
        if not self.verifier.verify_passport(passport):
            await self.telemetry.report(
                "plugin_verify.rejected",
                plugin_id,
                {
                    "reason": "Invalid passport signature",
                },
            )
            return {"approved": False, "reason": "Invalid passport signature"}

        # 3. Sandbox profiling (stub for production Kata integration)
        profile = await self._sandbox_profile(plugin_id, manifest)

        # 4. Trust evaluation
        trust_result = await self.evaluator.evaluate(
            source_id=plugin_id,
            identity_ok=True,
            capabilities_ok=True,
            profile_data=profile,
        )

        # 5. Register container hash for future attestation
        container_hash = profile.get("container_hash")
        if container_hash:
            self.verifier.register_container_hash(plugin_id, container_hash)

        if trust_result.action == "reject":
            await self.telemetry.report(
                "plugin_verify.rejected",
                plugin_id,
                {
                    "reason": "Behavioral trust score too low",
                    "score": trust_result.trust_score,
                },
            )
            return {
                "approved": False,
                "reason": "Behavioral trust score too low",
                "score": trust_result.trust_score,
            }

        await self.telemetry.report(
            "plugin_verify.approved",
            plugin_id,
            {
                "trust_score": trust_result.trust_score,
            },
        )
        return {
            "approved": True,
            "trust_score": trust_result.trust_score,
            "fingerprint": profile.get("fingerprint"),
        }

    async def _sandbox_profile(self, plugin_id: str, manifest: dict) -> dict:
        """Stub: run plugin in sandbox, collect metrics."""
        return {
            "network_domains": ["api.example.com"],
            "avg_memory_mb": 128,
            "spawn_behavior": "none",
            "filesystem_access": "read-only",
            "container_hash": "sha256:abc123",
            "fingerprint": {"risk_score": 0.04},
        }
