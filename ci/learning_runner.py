import os
import sys
import json

# Ensure ci module is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ci.memory import load_memory, save_memory
from ci.signature import extract_signature
from ci.predict import predict_fix
from ci.auto_apply import maybe_apply
from ci.learn import learn
from ci.prune import prune_dag

def run_adaptive_loop(dag, failures):
    """
    Core entry point for the predictive CI system.
    Processes each failure, predicts a fix, applies it, and learns.
    """
    if not failures:
        return dag, "SUCCESS"

    print(f"Adaptive Engine: Processing {len(failures)} failures...")
    
    memory = load_memory()
    retriable_nodes = []
    
    for f in failures:
        stderr = f.get("stderr", "")
        signature = extract_signature(stderr)
        
        print(f"Node '{f['node']}' failed. Signature: {signature}")
        
        patch_cmd, confidence = predict_fix(signature, memory)
        
        if patch_cmd:
            success = maybe_apply(patch_cmd, confidence)
            memory = learn(memory, signature, patch_cmd, success)
            
            if success:
                retriable_nodes.append(f["node"])
        else:
            print(f"No prediction available for signature of node '{f['node']}'.")

    save_memory(memory)
    
    if retriable_nodes:
        print(f"Adaptive Recovery: {len(retriable_nodes)} nodes healed via prediction. Recomputing DAG...")
        
        nodes = dag.get("compute_nodes", []) if isinstance(dag, dict) else dag
        if not nodes: nodes = dag.get("jobs", [])
        
        pruned_nodes = prune_dag(nodes, retriable_nodes)
        return {"compute_nodes": pruned_nodes}, "RETRY"

    return dag, "FAIL"

def main():
    if len(sys.argv) < 3:
        print("Usage: python learning_runner.py <dag.json> <failures.json>")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        dag = json.load(f)
    with open(sys.argv[2]) as f:
        failures = json.load(f)

    new_dag, status = run_adaptive_loop(dag, failures)
    
    # Save result for downstream steps
    result = {
        "status": status,
        "new_dag": new_dag
    }
    
    # Write summary for GitHub
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, 'a') as f:
            f.write("\n## 🧠 Adaptive Build Report\n")
            f.write(f"- Predictions made: {len(failures)}\n")
            f.write(f"- Status: {status}\n")

    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
