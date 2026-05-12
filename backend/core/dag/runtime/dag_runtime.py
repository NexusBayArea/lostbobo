from __future__ import annotations

import asyncio
import uuid
from typing import Any

from backend.core.dag.ir.dag_ir import DAGIR
from backend.core.dag.lineage.dag_lineage import DAGLineage
from backend.core.dag.replay.replay import DAGReplayer, DAGReplayRecorder
from backend.core.dag.runtime.execution_planner import ExecutionPlanner
from backend.core.scheduler.kernel_scheduler import KernelScheduler
from backend.core.scheduler.scheduler_models import ResourceRequest, Workload, WorkloadPriority, WorkloadType


class DAGRuntime:
    def __init__(self, kernel):
        self.kernel = kernel
        self.planner = ExecutionPlanner()
        self.scheduler: KernelScheduler = kernel.scheduler
        self.dag_registry = kernel.dag_registry
        self.lineage = DAGLineage(kernel.lineage_syscalls)
        self.replay_recorder = DAGReplayRecorder()
        self.replayer = DAGReplayer(self.replay_recorder, self.dag_registry)

    async def execute(self, dag: DAGIR, global_inputs: dict[str, Any] | None = None) -> dict[str, Any]:
        global_inputs = global_inputs or {}
        run_id = str(uuid.uuid4())
        await self.lineage.record_graph_start(dag.dag_id, run_id)

        if dag.replay and dag.replay.replay_hash:
            try:
                return await self.replayer.replay(dag, run_id)
            except KeyError:
                pass

        levels = self.planner.execution_plan(dag)
        outputs: dict[str, Any] = {}

        for node_ids in levels:
            tasks = [self._execute_node(dag, node_id, outputs, run_id, global_inputs) for node_id in node_ids]
            await asyncio.gather(*tasks)

        global_outputs = outputs.get(dag.nodes[-1].node_id, {}) if dag.nodes else {}
        await self.lineage.record_graph_end(dag.dag_id, run_id, global_outputs)
        return global_outputs

    async def _execute_node(self, dag: DAGIR, node_id: str, outputs: dict, run_id: str, global_inputs: dict):
        node = next(n for n in dag.nodes if n.node_id == node_id)
        await self.lineage.record_node_start(dag.dag_id, run_id, node.node_id)

        inputs = global_inputs.copy()
        for edge in dag.edges:
            if edge.target == node.node_id:
                inputs.update(outputs.get(edge.source, {}))

        workload = Workload(
            tenant_id=dag.tenant_id,
            plugin_name=node.plugin_name,
            workload_type=WorkloadType.DAG,
            priority=WorkloadPriority.NORMAL,
            resources=ResourceRequest(
                cpu_cores=node.resources.cpu_cores,
                memory_mb=node.resources.memory_mb,
                gpu_fraction=node.resources.gpu_fraction,
                gpu_type=node.resources.gpu_type,
            ),
            dag_id=dag.dag_id,
            dag_node_id=node.node_id,
        )

        sched_result = await self.scheduler.schedule(workload)
        if sched_result["status"] != "accepted":
            raise RuntimeError(f"Node {node.node_id} rejected")

        try:
            executor = self.dag_registry.get_executor(node.node_type)
            output = await executor(inputs)
            outputs[node.node_id] = output
            self.replay_recorder.record(node.node_id, inputs, output)
            await self.lineage.record_node_end(dag.dag_id, run_id, node.node_id, output, 0.0)
        finally:
            await self.scheduler.release_resources(workload)
