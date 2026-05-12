from __future__ import annotations

__all__ = [
    "ExecutionPriority",
    "ExecutionStatus",
    "ExecutionRequest",
    "ExecutionFuture",
    "KernelExecutionQueue",
    "LeaseTracker",
    "ResourceArbiter",
    "RunPodClient",
    "SimulationEvent",
    "SimulationStreamManager",
    "SimulationExecutor",
]


def __getattr__(name):
    import importlib

    _lazy_map = {
        "ExecutionPriority": "backend.core.execution.models",
        "ExecutionStatus": "backend.core.execution.models",
        "ExecutionRequest": "backend.core.execution.models",
        "ExecutionFuture": "backend.core.execution.models",
        "KernelExecutionQueue": "backend.core.execution.queue",
        "LeaseTracker": "backend.core.execution.queue",
        "ResourceArbiter": "backend.core.execution.arbitration",
        "RunPodClient": "backend.core.execution.runpod_client",
        "SimulationEvent": "backend.core.execution.streaming",
        "SimulationStreamManager": "backend.core.execution.streaming",
        "SimulationExecutor": "backend.core.execution.simulation_executor",
    }
    module_path = _lazy_map.get(name)
    if module_path is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    mod = importlib.import_module(module_path)
    return getattr(mod, name)
