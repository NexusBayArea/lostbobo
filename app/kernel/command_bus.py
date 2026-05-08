"""Command Bus — routes every command through the Kernel."""

from __future__ import annotations

import logging
from typing import Any, Dict

from backend.core.governance.service import get_governance

log = logging.getLogger(__name__)


class CommandBus:
    def __init__(self, kernel):
        self.kernel = kernel

    async def route(self, command: Dict[str, Any]) -> Any:
        cmd_type = command["type"]
        payload = command.get("payload", {})

        match cmd_type:
            case "MEMORY_RECORD":
                return await self.kernel.services["memory"].record(payload)
            case "MEMORY_QUERY":
                return await self.kernel.services["memory"].query(payload)
            case "MEMORY_RECONCILE":
                return await self.kernel.services["reconcile"].reconcile(
                    payload["decision_id"], payload["observed"]
                )
            case "WORLD_UPDATE":
                return await self.kernel.services["world"].update(payload)
            case "WORLD_SIMULATE":
                return await self.kernel.services["world"].simulate(payload)
            case "WORLD_PROPAGATE":
                return await self.kernel.services["world"].propagate_uncertainty(
                    payload
                )
            case "SKILL_EXECUTE":
                return await self.kernel.skills.execute(
                    payload["skill"], payload["input"]
                )
            case "AGENT_RUN":
                agent_name = payload["agent"]
                return await self.kernel.agents[agent_name].run(payload["input"])
            case "BUILD_PROMPT":
                return await self.kernel.prompt_stack.build(
                    payload["agent_id"], payload["query"], payload.get("mode")
                )
            case "SAFEGUARD_GATE":
                return await self.kernel.safeguards.gate_action(payload)
            case "MONITOR_METRIC":
                return await self.kernel.safeguards.monitor_metric(
                    payload["name"], payload["value"]
                )
            case "GOVERNANCE_CHECK":
                gov = get_governance()
                result = await gov.check(payload)
                if not result["allowed"]:
                    raise PermissionError(f"Governance blocked: {result['reason']}")
                return result
            case "AUTO_RESEARCH_RUN":
                return await self.kernel.auto_research.run_research_cycle(
                    payload["target"], payload["dsl"]
                )
            case "CHAOS_RUN_GAME_DAY":
                result = await self.kernel.services["chaos"].run_gameday(payload)
                await self.kernel.supabase_job_store.record_event(
                    "gameday_completed", result
                )
                return result
            case "LOAD_TEST_RUN":
                return await self.kernel.services["load"].run_load_test(payload)
            case "TRUST_VERIFY":
                result = await self.kernel.services["trust_runtime"].verify(payload)
                await self.kernel.supabase_job_store.save_trust_certificate(
                    {
                        "input_hash": hash(str(payload["input"])),
                        "trust_score": result.trust_score,
                        "provenance_hash": result.provenance_hash,
                        "risk_flags": result.risk_flags,
                        "tenant_id": payload.get("tenant_id"),
                    }
                )
                return result
            case "RECORD_OBSERVABILITY":
                return await self.kernel.services[
                    "observability"
                ].record_observability_event(payload)
            case "SAFETY_CHECK_EXECUTION":
                safety = self.kernel.services["safety"]
                result = await safety.check_execution(payload)
                await self.kernel.supabase_job_store.record_event(
                    "safety_check",
                    {
                        "job_id": payload.get("job_id"),
                        "safe": result.safe,
                        "action": result.action,
                        "reason": result.reason,
                    },
                )
                return result
            case "COGNITION_ATTEND":
                return await self.kernel.services["cognition"].attend(payload)
            case "COGNITION_ROUTE":
                return await self.kernel.services["cognition"].route(payload)
            case "COGNITION_ADD_NODE":
                return await self.kernel.services["cognition"].add_node(payload)
            case "RL_STEP":
                rl = self.kernel.services["rl"]
                return await rl.step(payload)
            case "SAH_RAG_QUERY":
                rag = self.kernel.services["sah_rag"]
                return await rag.query(payload.get("query"), payload.get("domain"), payload.get("top_k", 10))
            case _:
                # Fallback for unknown commands
                log.warning(f"Unknown command type: {cmd_type}")
                return await self.kernel.execute(command)
