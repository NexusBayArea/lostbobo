from backend.tools.runtime.backends.registry import BACKENDS
from backend.tools.runtime.backends.registry import BACKENDS
from backend.tools.runtime.trace import record
from backend.tools.runtime.contract import compute_contract
from backend.tools.runtime.cache import lookup_contract

class ExecutionEngine:
    def run_node(self, node, context, upstream_contracts):
        contract = compute_contract(node, upstream_contracts)

        # STEP 1: cross-run cache lookup
        cached = lookup_contract(contract)
        if cached:
            return {"result": cached, "meta": {"cache_hit": True}}

        # STEP 2: execute normally
        backend = BACKENDS[node["type"]]
        result = backend.execute(node, context)
        
        # STEP 3: persist
        record(node["id"], contract, node.get("deps", []), result, context)
        
        return {"result": result, "meta": {"cache_hit": False}}

def run_dag(nodes, context):
    engine = ExecutionEngine()
    results = {}
    contracts = {}

    for node in nodes:
        # Pass contracts to engine for contract computation
        execution_response = engine.run_node(node, context, contracts)
        results[node["id"]] = execution_response["result"]
        # Store computed contract for downstream nodes
        contracts[node["id"]] = compute_contract(node, contracts)

    return results

