from __future__ import annotations

import logging
from typing import Any

from backend.core.auth.models import AuthContext, Role
from backend.core.governance.service import get_governance

log = logging.getLogger(__name__)


class PolicyEngine:
    """
    Advanced contextual authorization engine.
    Combines RBAC + compute cost + tenant rules.
    """

    async def evaluate(self, ctx: AuthContext, request: dict[str, Any]) -> dict[str, Any]:
        """Main policy decision point"""
        action = request.get("action", "read")
        resource = request.get("resource", "unknown")
        estimated_cost = request.get("estimated_cost", 0)

        # 1. Tenant Check (Non-negotiable)
        if ctx.tenant_id == "public" and resource in ["simulation", "admin", "internal"]:
            if Role.admin not in ctx.roles:
                return {"allowed": False, "reason": "public_tenant_restricted"}

        # 2. RBAC Baseline
        if not self._rbac_allows(ctx, action, resource):
            return {"allowed": False, "reason": "insufficient_role"}

        # 3. Compute-Aware Policies
        if resource == "simulation" and estimated_cost > 30:
            if not ctx.can_access_simulation(estimated_cost):
                return {"allowed": False, "reason": "simulation_cost_exceeds_role"}

        # 4. Agent / A2A Restrictions
        if ctx.agent_id and request.get("agent_hops", 0) > 5:
            return {"allowed": False, "reason": "max_agent_hops_exceeded"}

        # 5. Governance Pre-check
        gov = get_governance()
        gov_result = await gov.check(
            {
                "tenant_id": ctx.tenant_id,
                "user_id": ctx.user_id,
                "operation": resource,
                "estimated_tokens": request.get("estimated_tokens", 400),
                "agent_hops": request.get("agent_hops", 0),
            }
        )

        if not gov_result["allowed"]:
            return {"allowed": False, "reason": gov_result["reason"]}

        return {"allowed": True, "context": ctx.model_dump()}

    def _rbac_allows(self, ctx: AuthContext, action: str, resource: str) -> bool:
        if Role.admin in ctx.roles:
            return True

        role_map = {
            Role.analyst: {"read", "simulate", "retrieve"},
            Role.plugin_dev: {"read", "write", "plugin"},
            Role.viewer: {"read"},
        }

        allowed_actions = role_map.get(ctx.roles[0] if ctx.roles else Role.viewer, set())
        return action in allowed_actions

    def is_capability_allowed(self, plugin_id: str, capability: str) -> bool:
        """Check if a capability is permitted for the given plugin in the trust zone."""
        from backend.core.sdk.abi.plugin_manifest import PluginPermission

        allowed_map: dict[str, set[str]] = {
            Role.admin.value: {c.value for c in PluginPermission},
            Role.analyst.value: {
                "dag.execute",
                "memory.read",
                "storage.read",
                "network.egress",
                "kernel.events",
            },
            Role.viewer.value: {
                "memory.read",
                "storage.read",
                "kernel.events",
            },
            Role.plugin_dev.value: {
                "dag.execute",
                "memory.read",
                "memory.write",
                "storage.read",
                "storage.write",
                "network.egress",
                "kernel.events",
                "lineage.write",
            },
        }

        plugin = getattr(self, "_trust_store", None)
        if plugin is None:
            if hasattr(self, "_kernel") and hasattr(self._kernel, "trust_store"):
                plugin = self._kernel.trust_store.get_plugin(plugin_id)

        if plugin and plugin.permissions:
            return capability in plugin.permissions

        ctx_roles = getattr(self, "_default_roles", [Role.viewer])
        allowed = allowed_map.get(ctx_roles[0].value, set())
        return capability in allowed


# Singleton
_policy_engine: PolicyEngine | None = None


def get_policy_engine() -> PolicyEngine:
    global _policy_engine
    if _policy_engine is None:
        _policy_engine = PolicyEngine()
    return _policy_engine
