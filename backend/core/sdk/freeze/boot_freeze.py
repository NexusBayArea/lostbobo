"""
Boot-time registration of all frozen SDK contracts.
Call `freeze_all(registry)` once during kernel initialisation.
"""

from backend.core.sdk.contracts.dag.dag_contract import DAGNodeContract
from backend.core.sdk.contracts.events.event_contract import KernelEvent
from backend.core.sdk.contracts.execution.execution_contract import ExecutionContract
from backend.core.sdk.contracts.lineage.lineage_contract import LineageContract
from backend.core.sdk.contracts.scheduler.scheduler_contract import SchedulerDispatchContract
from backend.core.sdk.contracts.state.state_contract import StateSnapshotContract
from backend.core.sdk.freeze.frozen_schema_registry import FrozenSchemaRegistry


def freeze_all(registry: FrozenSchemaRegistry, kernel_abi_version: str):
    registry.register("kernel_event", kernel_abi_version, KernelEvent)
    registry.register("dag_node", kernel_abi_version, DAGNodeContract)
    registry.register("execution_payload", kernel_abi_version, ExecutionContract)
    registry.register("state_snapshot", kernel_abi_version, StateSnapshotContract)
    registry.register("lineage_record", kernel_abi_version, LineageContract)
    registry.register("scheduler_dispatch", kernel_abi_version, SchedulerDispatchContract)
