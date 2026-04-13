import os
import sys
import json
import glob

# Ensure ci module is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ci.policy_runner import evaluate_policies

def main():
    if len(sys.argv) > 1:
        dag_file = sys.argv[1]
    else:
        dag_file = "dag.json"

    try:
        with open(dag_file, 'r') as f:
            dag_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: {dag_file} not found.", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: {dag_file} is not valid JSON.", file=sys.stderr)
        sys.exit(1)

    policy_nodes = dag_data.get("policy_nodes", [])
    policies_report = []
    
    # We will expand context inputs per node
    for node in policy_nodes:
        inputs = node.get("inputs", [])
        files = []
        for input_path in inputs:
            # simple globbing / directory walking
            if os.path.isdir(input_path):
                for root, _, filenames in os.walk(input_path):
                    for filename in filenames:
                        files.append(os.path.join(root, filename))
            elif os.path.isfile(input_path):
                files.append(input_path)
            elif "*" in input_path:
                files.extend(glob.glob(input_path, recursive=True))
                
        context = {"files": files}
        
        # We can use our runner per node
        from ci.policy_runner import run_policy
        res = run_policy(node, context)
        
        # Add files field manually as per prompt requirement
        if res["result"] == "FAIL":
            res["files"] = files
            
        policies_report.append(res)
    
    dashboard = {
        "policies": policies_report
    }
    
    print(json.dumps(dashboard, indent=2))
    
    # Write to github step summary
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, 'a') as f:
            f.write("## CI Policy Report\n")
            for res in policies_report:
                f.write(f"- {res['policy']}: {res['result']}\n")
                
    has_failure = any(res["result"] == "FAIL" for res in policies_report)
    if has_failure:
        sys.exit(1)

if __name__ == "__main__":
    main()
