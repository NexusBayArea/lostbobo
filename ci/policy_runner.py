import json
import os
import sys

# Ensure policies module is found correctly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ci.policies.registry import POLICIES

def run_policy(node, context):
    rule = node.get("rule")
    fn = POLICIES.get(rule)

    if not fn:
        return {
            "policy": node.get("name"),
            "result": "FAIL",
            "reason": f"Unknown rule: {rule}"
        }

    # Pass the context or files based on node inputs
    # Some rules might take files, others might take something else
    # For now we'll pass whatever files we found based on inputs
    files = context.get("files", [])
    
    try:
        result = fn(files)
    except Exception as e:
        print(f"Error executing rule {rule}: {e}")
        result = False

    return {
        "policy": node.get("name"),
        "result": "PASS" if result else "FAIL"
    }

def evaluate_policies(dag_data, context):
    results = {}
    
    # We might look at 'policy_nodes' in the dag_data dictionary
    policy_nodes = dag_data.get("policy_nodes", [])
    
    for node in policy_nodes:
        if node.get("type", "policy") == "policy" or "rule" in node:
            results[node["name"]] = run_policy(node, context)

    return results
