import json
import os
import sys

# Ensure ci module is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ci.heal_dag import self_heal
from ci.prune import prune_dag

def run_self_healing(dag, failures):
    """
    Orchestrates the self-healing loop.
    Returns: (new_dag, status)
    """
    if not failures:
        return dag, "SUCCESS"

    print(f"Autonomous System: {len(failures)} failures detected. Initiating diagnostic probe...")

    fix_count = self_heal(failures)
    
    if fix_count > 0:
        print(f"Self-Healing: {fix_count} patches applied. Re-calculating pruned DAG for retry...")
        
        # We need the full node list to prune correctly
        # In this simplified model, we'll assume 'dag' passed in is the list of nodes
        # If it's the full dict {"jobs": [...]} we handle it
        nodes = dag.get("jobs", []) if isinstance(dag, dict) else dag
        
        failed_names = [f["node"] for f in failures]
        pruned_nodes = prune_dag(nodes, failed_names)
        
        # Return the new execution plan
        return {"jobs": pruned_nodes}, "RETRY"
    
    print("Self-Healing: No reliable patches could be generated for the detected failures.")
    return dag, "FAIL"

def main():
    # This might be called via CLI with failure artifacts
    if len(sys.argv) < 3:
        print("Usage: python self_healing_runner.py <dag.json> <failures.json>")
        sys.exit(1)

    dag_path = sys.argv[1]
    failures_path = sys.argv[2]

    try:
        with open(dag_path) as f:
            dag = json.load(f)
        with open(failures_path) as f:
            failures = json.load(f)
    except Exception as e:
        print(f"Error loading context: {e}")
        sys.exit(1)

    new_dag, status = run_self_healing(dag, failures)
    
    # Output the result for the next Step
    result = {
        "status": status,
        "failures": len(failures),
        "fixes": sum(1 for f in failures if f.get("fixed", False)), # This would be tracked in a real system
        "new_dag": new_dag
    }
    
    print(json.dumps(result, indent=2))
    
    # Sync with GitHub Summary
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, 'a') as f:
            f.write("\n## Autonomous Self-Healing Report\n")
            f.write(f"- Failures detected: {len(failures)}\n")
            f.write(f"- Status: {status}\n")
            if status == "RETRY":
                f.write(f"- Re-run scope: {len(new_dag.get('jobs', []))} nodes\n")

if __name__ == "__main__":
    main()
