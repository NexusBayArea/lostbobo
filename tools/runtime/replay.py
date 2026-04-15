from typing import Dict, Any, List
# Since Executor isn't fully defined in a single file in this structure,
# we rely on the kernel's execution model.
# Replay assumes access to the system dispatcher.

class ReplayEngine:
    def __init__(self, plan):
        self.plan = plan

    def replay_full(self, trace_data: Dict[str, Any], dispatch, context=None):
        """
        Re-run entire DAG deterministically using trace inputs.
        """
        context = context or {}

        # seed state from trace
        seed = self._build_seed(trace_data)

        # Re-run nodes using seed as context/inputs
        results = {}
        for node_name in self.plan.get("nodes", {}):
            results[node_name] = dispatch(self.plan["nodes"][node_name], seed.get(node_name, {}).get("inputs", {}), context)
        return results

    def replay_node(self, node_name: str, trace_data: Dict[str, Any], dispatch, context=None):
        """
        Replay a single node using historical inputs.
        """
        context = context or {}

        node_trace = trace_data.get("nodes", {}).get(node_name)
        if not node_trace:
            raise ValueError(f"No trace found for node {node_name}")

        node = self.plan.get("nodes", {}).get(node_name)
        if not node:
             raise ValueError(f"Node {node_name} not found in plan")

        return dispatch(node, node_trace.get("inputs", {}), context)

    def replay_failed(self, trace_data: Dict[str, Any], dispatch, context=None):
        """
        Replay only failed nodes.
        """
        context = context or {}

        failed = [name for name, data in trace_data.get("nodes", {}).items() if data.get("status") == "failed"]

        results = {}
        for node_name in failed:
            node = self.plan.get("nodes", {}).get(node_name)
            results[node_name] = dispatch(node, trace_data.get("nodes", {}).get(node_name, {}).get("inputs", {}), context)

        return results

    def _build_seed(self, trace_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert trace into reproducible state snapshot.
        """
        seed = {}
        for name, data in trace_data.get("nodes", {}).items():
            seed[name] = {
                "inputs": data.get("inputs", {}),
                "outputs": data.get("outputs", {}),
                "status": data.get("status"),
            }
        return seed
