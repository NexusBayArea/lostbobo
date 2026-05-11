# backend/core/hardware/mig/controller.py
from __future__ import annotations

import asyncio

from backend.core.hardware.forecasting import PredictiveCapacityForecaster
from backend.core.services.observability_service import observability
from backend.core.tracing import trace_context


class MIGProfileController:
    """
    Automated MIG profile switching based on demand, regime, and SLA.
    Runs as a Kubernetes CronJob every 5 minutes.
    """

    PROFILES = {
        "all-1g.5gb": {
            "profile": "1g.5gb",
            "count": 7,
            "suitable_for": ["defense", "high-density", "isolated"],
            "priority": 100,
        },
        "all-2g.10gb": {
            "profile": "2g.10gb",
            "count": 3,
            "suitable_for": ["enterprise"],
            "priority": 80,
        },
        "all-3g.20gb": {
            "profile": "3g.20gb",
            "count": 2,
            "suitable_for": ["large-sim", "high-memory"],
            "priority": 70,
        },
        "mixed": {
            "profile": "mixed",
            "count": 1,
            "suitable_for": ["general"],
            "priority": 50,
        },
    }

    async def reconcile(self) -> None:
        """Main reconciliation loop."""
        with trace_context("mig.reconcile") as span:
            try:
                state = await self._get_current_state()
                demand = await PredictiveCapacityForecaster.forecaster().predict_capacity(horizon_minutes=60)

                nodes = await self._get_mig_capable_nodes()

                for node in nodes:
                    current = await self._get_current_mig_profile(node)
                    target = self._decide_best_profile(demand, state.get("regime", "normal"))

                    if current != target:
                        await self._switch_profile(node, target)
                        observability().increment("mig_profile_switches")

                span.set_attribute("nodes_processed", len(nodes))
                observability().gauge("mig_reconcile_success", 1)

            except Exception as e:
                observability().increment("mig_reconcile_failures")
                span.set_attribute("error", str(e))

    async def _get_current_state(self) -> dict:
        """Get current system state."""
        try:
            from backend.core.runtime.state_registry.service import StateRegistryService

            return await StateRegistryService.registry().get_current()
        except Exception:
            return {"regime": "normal"}

    def _decide_best_profile(self, demand: dict, regime: str) -> str:
        """Decide optimal MIG profile based on current demand and regime."""
        if regime in ("panic", "disruption") or demand.get("isolated", 0) > 0.7:
            return "all-1g.5gb"

        if demand.get("high_memory", 0) > 0.6:
            return "all-3g.20gb"

        if demand.get("dedicated", 0) > 0.5:
            return "all-2g.10gb"

        return "mixed"

    async def _get_mig_capable_nodes(self) -> list[str]:
        """Return list of nodes with MIG capability."""
        try:
            k8s = await self._get_k8s_client()
            return await k8s.list_mig_nodes()
        except Exception:
            return []

    async def _get_current_mig_profile(self, node_name: str) -> str:
        """Get current MIG profile on a node."""
        try:
            k8s = await self._get_k8s_client()
            result = await k8s.exec_on_node(node_name, "nvidia-smi mig -lgi | head -n 1")
            return result.strip() or "mixed"
        except Exception:
            return "mixed"

    async def _switch_profile(self, node_name: str, target_profile: str) -> None:
        """Switch MIG profile on a node."""
        print(f"[MIG] Switching {node_name} to {target_profile}")

        k8s = await self._get_k8s_client()

        await k8s.drain_node(node_name, timeout=600)

        await k8s.exec_on_node(
            node_name,
            f"nvidia-smi mig -cgi {self.PROFILES[target_profile]['profile']} -e",
        )

        await k8s.reboot_node(node_name)

        await asyncio.sleep(180)
        await k8s.uncordon_node(node_name)

        observability().increment("mig_profile_switched")

    async def _get_k8s_client(self):
        """Get K8s client."""
        try:
            from backend.core.services.k8s_client import get_k8s_client

            return get_k8s_client()
        except Exception:
            return None
