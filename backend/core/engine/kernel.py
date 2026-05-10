# backend/core/engine/kernel.py
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from backend.core.engine.agent_contracts import get_agent_registry
from backend.core.engine.evaluation_layer import get_evaluation_harness
from backend.core.engine.event_bus import get_event_bus
from backend.core.engine.guild_rails import get_plugin_guild
from backend.core.engine.probability_runtime import get_calibration_pipeline
from backend.core.engine.secrets import get_core_secrets
from backend.core.engine.state_fabric import get_state_fabric
from backend.core.kernel.lineage.collector import LineageCollector


class CoreKernel:
    def __init__(self) -> None:
        self._booted = False
        self._boot_time: str | None = None
        self._subsystems: dict[str, bool] = {}

    async def boot(self) -> None:
        if self._booted:
            return

        print("[Kernel] Booting SimHPC Core Engine...")

        # 1. Secrets (Infisical)
        try:
            await get_core_secrets()
            self._subsystems["secrets"] = True
            print("[Kernel] ✅ Secrets (Infisical)")
        except Exception as e:
            self._subsystems["secrets"] = False
            print(f"[Kernel] ⚠️ Secrets unavailable: {e}")

        # 2. Event Bus
        try:
            bus = get_event_bus()
            await bus.start()
            self._subsystems["event_bus"] = True
            print("[Kernel] ✅ Event Bus")
        except Exception as e:
            self._subsystems["event_bus"] = False
            print(f"[Kernel] ❌ Event Bus failed: {e}")

        # 3. State Fabric
        try:
            fabric = get_state_fabric()
            await fabric.start()
            self._subsystems["state_fabric"] = True
            print("[Kernel] ✅ State Fabric (reconciled from Supabase)")
        except Exception as e:
            self._subsystems["state_fabric"] = False
            print(f"[Kernel] ❌ State Fabric failed: {e}")

        # 4. Calibration Pipeline
        try:
            cal = get_calibration_pipeline()
            await cal.start()
            self._subsystems["calibration"] = True
            print("[Kernel] ✅ Calibration Pipeline")
        except Exception as e:
            self._subsystems["calibration"] = False
            print(f"[Kernel] ❌ Calibration failed: {e}")

        # 5. Agent Registry
        try:
            registry = get_agent_registry()
            await registry.start()
            self._subsystems["agent_registry"] = True
            print("[Kernel] ✅ Agent Registry")
        except Exception as e:
            self._subsystems["agent_registry"] = False
            print(f"[Kernel] ❌ Agent Registry failed: {e}")

        # 6. Evaluation Harness
        try:
            harness = get_evaluation_harness()
            await harness.start()
            self._subsystems["evaluation"] = True
            print("[Kernel] ✅ Evaluation Harness")
        except Exception as e:
            self._subsystems["evaluation"] = False
            print(f"[Kernel] ❌ Evaluation Harness failed: {e}")

        # 7. Plugin Guild
        try:
            guild = get_plugin_guild()
            await guild.start()
            self._subsystems["plugin_guild"] = True
            print("[Kernel] ✅ Plugin Guild")
        except Exception as e:
            self._subsystems["plugin_guild"] = False
            print(f"[Kernel] ❌ Plugin Guild failed: {e}")

        # 8. Lineage Collector (NEW)
        try:
            _ = LineageCollector.collector()
            self._subsystems["lineage"] = True
            print("[Kernel] ✅ Lineage Collector (full provenance)")
        except Exception as e:
            self._subsystems["lineage"] = False
            print(f"[Kernel] ⚠️ Lineage Collector failed: {e}")

        self._booted = True
        self._boot_time = datetime.now(UTC).isoformat()

        # Publish boot health event
        await self._publish_boot_event()

        healthy = sum(self._subsystems.values())
        total = len(self._subsystems)
        print(f"[Kernel] Boot complete: {healthy}/{total} subsystems healthy")

    async def shutdown(self) -> None:
        print("[Kernel] Shutting down...")

        # Graceful shutdown order (reverse boot)
        for name in reversed(list(self._subsystems.keys())):
            try:
                if name == "event_bus":
                    bus = get_event_bus()
                    await bus.stop()
                elif name == "agent_registry":
                    registry = get_agent_registry()
                    await registry.terminate_all()
            except Exception:
                pass

        self._booted = False
        print("[Kernel] Shutdown complete.")

    def health(self) -> dict[str, Any]:
        return {
            "booted": self._booted,
            "boot_time": self._boot_time,
            "subsystems": self._subsystems,
            "healthy": all(self._subsystems.values()),
            "subsystem_count": len(self._subsystems),
            "healthy_count": sum(self._subsystems.values()),
        }

    async def _publish_boot_event(self) -> None:
        try:
            from backend.core.engine.event_bus import CoreEvent, Topics

            bus = get_event_bus()
            await bus.publish(
                CoreEvent(
                    topic=Topics.SYSTEM_HEALTH_CHECK,
                    payload=self.health(),
                    source="kernel",
                ).seal()
            )
        except Exception:
            pass


_kernel: CoreKernel | None = None


def get_kernel() -> CoreKernel:
    global _kernel
    if _kernel is None:
        _kernel = CoreKernel()
    return _kernel
