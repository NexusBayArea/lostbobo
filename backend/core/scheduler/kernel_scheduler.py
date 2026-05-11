from __future__ import annotations

from typing import Any

from backend.core.hardware.isolation import GPUIsolationManager
from backend.core.scheduler.arbitration_engine import ArbitrationEngine
from backend.core.scheduler.budget_engine import BudgetEngine
from backend.core.scheduler.fairness_engine import FairnessEngine
from backend.core.scheduler.preemption_engine import PreemptionEngine
from backend.core.scheduler.queue_manager import QueueManager
from backend.core.scheduler.replay_scheduler import ReplayScheduler
from backend.core.scheduler.resource_graph import ResourceGraph
from backend.core.scheduler.scheduler_models import SchedulingDecision, Workload
from backend.core.scheduler.sla_engine import SLAEngine
from backend.core.scheduler.speculative_engine import SpeculativeExecutionEngine
from backend.core.scheduler.thermal_engine import ThermalEngine


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
            result = await self.schedule(next_wl)
            if result["status"] != SchedulingDecision.ACCEPTED:
                await self.queues.enqueue(next_wl[0].priority.value, next_wl[1])
