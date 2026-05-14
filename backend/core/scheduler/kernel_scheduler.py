from __future__ import annotations

import logging
from typing import Any

from backend.core.hardware.isolation import GPUIsolationManager
from backend.core.scheduler.arbitration_engine import ArbitrationEngine
from backend.core.scheduler.budget_engine import BudgetEngine
from backend.core.scheduler.fairness_engine import FairnessEngine
from backend.core.scheduler.preemption_engine import PreemptionEngine
from backend.core.scheduler.queue_manager import QueueManager
from backend.core.scheduler.replay_scheduler import ReplayScheduler
from backend.core.scheduler.resource_graph import ResourceGraph
from backend.core.scheduler.scheduler_models import (
    ResourceRequest,
    SchedulingDecision,
    Workload,
    WorkloadPriority,
    WorkloadType,
)
from backend.core.scheduler.sla_engine import SLAEngine
from backend.core.scheduler.speculative_engine import SpeculativeExecutionEngine
from backend.core.scheduler.thermal_engine import ThermalEngine

logger = logging.getLogger(__name__)


class KernelScheduler:
    def __init__(self, gpu_manager: GPUIsolationManager):
        self.resources = ResourceGraph()
        self.queues = QueueManager()
        self.fairness = FairnessEngine()
        self.budgets = BudgetEngine()
        self.sla = SLAEngine()
        self.thermal = ThermalEngine()
        self.speculative = SpeculativeExecutionEngine()
        self.preemption = PreemptionEngine()
        self.replay = ReplayScheduler()
        self.arbitration = ArbitrationEngine(fairness=self.fairness, budgets=self.budgets, thermal=self.thermal)
        self.gpu_manager = gpu_manager
        self.active_workloads: dict[str, Workload] = {}
        self.capability_registry = None

    async def schedule(self, workload: Workload) -> dict[str, Any]:
        if not await self.arbitration.evaluate(workload):
            await self.queues.enqueue(workload.priority.value, workload)
            return {"status": SchedulingDecision.QUEUED}

        candidates = self.resources.available_nodes(workload.resources)
        if not candidates:
            victim_idx = self.preemption.select_victim(workload, list(self.active_workloads.items()))
            if victim_idx is not None:
                victim_wl = list(self.active_workloads.values())[victim_idx]
                await self.release_resources(victim_wl)
                del self.active_workloads[victim_wl.workload_id]
                candidates = self.resources.available_nodes(workload.resources)
                if not candidates:
                    await self.queues.enqueue(workload.priority.value, workload)
                    return {"status": SchedulingDecision.QUEUED}
            else:
                await self.queues.enqueue(workload.priority.value, workload)
                return {"status": SchedulingDecision.QUEUED}

        best = self.thermal.select_best(candidates, workload)
        if best is None:
            await self.queues.enqueue(workload.priority.value, workload)
            return {"status": SchedulingDecision.QUEUED}
        selected_node_id, selected_node, _ = best

        if workload.resources.gpu_fraction > 0:
            try:
                gpu_allocation = await self.gpu_manager.allocate_gpu(
                    tenant_id=workload.tenant_id,
                    required_fraction=workload.resources.gpu_fraction,
                    gpu_type=workload.resources.gpu_type,
                )
            except Exception as e:
                await self.queues.enqueue(workload.priority.value, workload)
                return {"status": SchedulingDecision.REJECTED, "reason": str(e)}
        else:
            gpu_allocation = None

        selected_node.allocate(workload.resources)
        self.fairness.record_usage(workload.tenant_id, workload.resources.gpu_fraction)
        self.active_workloads[workload.workload_id] = workload

        replay_hash = self.replay.compute_hash(workload)
        self.replay.record_placement(workload.workload_id, selected_node_id, workload.resources.gpu_fraction)

        return {
            "status": SchedulingDecision.ACCEPTED,
            "node": selected_node_id,
            "gpu_allocation": gpu_allocation,
            "replay_hash": replay_hash,
        }

    async def release_resources(self, workload: Workload):
        if workload.resources.gpu_fraction > 0:
            await self.gpu_manager.release_gpu(workload.tenant_id, workload.resources.gpu_fraction)
        self.fairness.release(workload.tenant_id, workload.resources.gpu_fraction)
        self.active_workloads.pop(workload.workload_id, None)

    async def run_queue(self):
        while True:
            next_wl = await self.queues.dequeue()
            if next_wl is None:
                break
            result = await self.schedule(next_wl[1])
            if result["status"] != SchedulingDecision.ACCEPTED:
                await self.queues.enqueue(next_wl[0], next_wl[1])

    async def schedule_capability(
        self,
        capability: str,
        payload: dict[str, Any],
        *,
        tenant_id: str = "default",
        priority: WorkloadPriority = WorkloadPriority.NORMAL,
    ) -> Any:
        entry = None
        if self.capability_registry:
            entry = self.capability_registry.get_entry(capability)

        gpu_profile = getattr(entry, "required_gpu_profile", None)
        estimated_memory = getattr(entry, "estimated_memory_mb", 256) if entry else 256

        if gpu_profile and str(gpu_profile.value) not in ("none", ""):
            gpu_fraction = {
                "shared-small": 0.25,
                "shared-medium": 0.50,
                "shared-large": 0.75,
                "dedicated-single": 1.0,
            }.get(gpu_profile.value, 0.0)
        else:
            gpu_fraction = 0.0

        workload = Workload(
            tenant_id=tenant_id,
            plugin_name=entry.plugin_name if entry else "unknown",
            workload_type=WorkloadType.INFERENCE,
            priority=priority,
            resources=ResourceRequest(
                cpu_cores=1.0,
                memory_mb=estimated_memory,
                gpu_fraction=gpu_fraction,
                max_runtime_seconds=getattr(entry, "timeout_seconds", 300) if entry else 300,
            ),
        )

        decision = await self.schedule(workload)

        if decision["status"] == SchedulingDecision.REJECTED:
            raise RuntimeError(f"Capability '{capability}' rejected: {decision.get('reason')}")

        if decision["status"] == SchedulingDecision.QUEUED:
            raise RuntimeError(f"Capability '{capability}' queued (no resources available)")

        if self.capability_registry:
            result = await self.capability_registry.invoke(
                capability=capability,
                payload=payload,
                tenant_id=tenant_id,
            )
            return result

        return {"status": "accepted", "decision": decision}
